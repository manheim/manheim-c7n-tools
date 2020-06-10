# Copyright 2017-2019 Manheim / Cox Automotive
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Script to scan CloudWatch metrics, logs, and Dead Letter SQS queue for all
cloud-custodian lambda functions, and print info and logs and exit non-zero if
any failed or errored.
"""

import sys
import argparse
import logging
import boto3
from botocore.config import Config
import re
from time import time, sleep
from datetime import datetime, timedelta, tzinfo
from operator import itemgetter

from manheim_c7n_tools.utils import (
    set_log_info, set_log_debug, red, green, assume_role
)
from manheim_c7n_tools.version import VERSION, PROJECT_URL
from manheim_c7n_tools.config import ManheimConfig

FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger = logging.getLogger()

# suppress boto3 internal logging below WARNING level
boto3_log = logging.getLogger("boto3")
boto3_log.setLevel(logging.WARNING)
boto3_log.propagate = True

# suppress botocore internal logging below WARNING level
botocore_log = logging.getLogger("botocore")
botocore_log.setLevel(logging.WARNING)
botocore_log.propagate = True

# Override max attempts for botocore retry configuration, to cope with
# throttling. This  constant is used in two different places below...
BOTOCORE_MAX_ATTEMPTS = 10


class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)


class LambdaHealthChecker(object):
    """Class for checking Lambda func health via CloudWatch"""

    # If a log message meets this exact regex, skip over it
    NO_OWNER_EMAIL_LOOKUP_WARNING = re.compile(
        r'.*(ERROR|WARNING).*unable to lookup owner email.*'
        'Please configure LDAP or org_domain')

    req_id_re = re.compile(
        r'^(START|END|REPORT|\S+\s\S+)\s'
        r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}).*'
    )

    def __init__(self, func_name, region_name, logs=None, cw=None):
        """
        Initialize LambdaHealthChecker

        :param func_name: Lambda function name
        :type func_name: str
        :param region_name: name of the region to run against
        :type region_name: str
        :param logs: boto3 "logs" service client, or None to create new
        :type logs: boto3.client
        :param cw: boto3 "cloudwatch" Service Resource, or None to create new
        :type cw: boto3.resource
        """
        self._func_name = func_name
        if logs is None:
            # override default max_attempts from 5 to 10, for throttling
            retry_conf = Config(
                retries={'max_attempts': BOTOCORE_MAX_ATTEMPTS})
            self._logs = boto3.client(
                'logs', config=retry_conf, region_name=region_name
            )
        else:
            self._logs = logs
        if cw is None:
            self._cw = boto3.resource('cloudwatch', region_name=region_name)
        else:
            self._cw = cw

    def get_filtered_logs(
            self, request_ids, interval=86400, group_name=None,
            always_match_re=None, never_match_re=None
    ):
        """
        Get CloudWatch logs for the last ``interval`` seconds and return only
        those entries with messages matching ``filter_re``.

        :param request_ids: list of str request IDs to get logs for
        :type request_ids: list
        :param group_name: CloudWatch logs group name. If left at default of
          ``None``, defaults to ``/aws/lambda/{func_name}``.
        :type group_name: str
        :param interval: how far back in logs to look, in seconds
        :type interval: int
        :param always_match_re: Regex for logs to ALWAYS return
        :type always_match_re: ``re``
        :param never_match_re: Regex for logs to NEVER return, even if they
          match ``always_match_re``.
        :type never_match_re: ``re``
        :return: dict of request_id to list of log entry dicts
        :rtype: dict
        """
        logs = self.get_cloudwatch_logs(
            interval=interval, group_name=group_name
        )
        if group_name is None:
            group_name = '/aws/lambda/%s' % self._func_name
        result = {}
        matchcount = 0
        for log in logs:
            m = self.req_id_re.match(log['message'])
            if always_match_re is None:
                always_m = None
            else:
                # if the regex is found, then skip this log and continue
                noelw = re.match(self.NO_OWNER_EMAIL_LOOKUP_WARNING,
                                 log['message'])
                if noelw:
                    continue
                always_m = always_match_re.match(log['message'])
            if m is None and always_m is None:
                logger.debug(
                    'Event %s in group %s stream %s does not match '
                    'RequestId regex: %s', log['eventId'], group_name,
                    log['logStreamName'], log['message']
                )
                continue
            if m is not None:
                req_id = m.group(2)
                if req_id in request_ids:
                    log['logGroupName'] = group_name
                    if req_id not in result:
                        result[req_id] = []
                    result[req_id].append(log)
                    matchcount += 1
            if always_m is not None:
                if (
                    never_match_re is not None and
                    never_match_re.match(log['message'])
                ):
                    logger.debug(
                        'Message matched always_match_re but also '
                        'never_match_re; suppressing: %s', log['message']
                    )
                    continue
                if 'always_match' not in result:
                    result['always_match'] = []
                result['always_match'].append(log)
        logger.debug(
            'Filtered %d log messages to %d messages from %d invocations',
            len(logs), matchcount, len(result)
        )
        return result

    def get_cloudwatch_logs(self, interval=86400, group_name=None):
        """
        Get CloudWatch logs for the last ``interval`` seconds. The log group
        name defaults to ``/aws/lambda/{func_name}`` if left at the default of
        None.

        :param group_name: CloudWatch logs group name. If left at default of
          ``None``, defaults to ``/aws/lambda/{func_name}``.
        :type group_name: str
        :param interval: how far back in logs to look, in seconds
        :type interval: int
        :return: list of log entry dicts, sorted by timestamp
        :rtype: list
        """
        interval = interval * 1000  # milliseconds
        now = int(time()) * 1000
        cutoff = now - interval
        if group_name is None:
            group_name = '/aws/lambda/%s' % self._func_name
        logger.debug('Finding streams in CW Log Group: %s', group_name)
        paginator = self._logs.get_paginator('describe_log_streams')
        stream_iterator = paginator.paginate(
            logGroupName=group_name,
            orderBy='LastEventTime',
            descending=True
        )
        streams = []
        try:
            for resp in stream_iterator:
                for stream in resp['logStreams']:
                    if stream.get('lastEventTimestamp', 0) < cutoff:
                        continue
                    streams.append(stream['logStreamName'])
        except Exception as ex:
            if hasattr(ex, 'response'):
                emsg = ex.response.get('Error', {}).get('Code', 'unknown')
                if emsg == 'ResourceNotFoundException':
                    logger.warning('CloudWatch Log group does not exist: %s',
                                   group_name)
                    return []
            raise
        logger.debug('Found %d log streams with events in time span',
                     len(streams))
        logs = []
        for sname in streams:
            logs.extend(self._get_cw_log_stream(
                group_name,
                sname,
                cutoff,
                now
            ))
        return sorted(logs, key=itemgetter('timestamp'))

    def _get_cw_log_stream(self, group_name, stream_name, start_ts, end_ts):
        """
        Return all log messages from the specified stream at or after ``ts``.

        :param group_name: CloudWatch log group name
        :type group_name: str
        :param stream_name: CloudWatch log stream name
        :type stream_name: str
        :param start_ts: timestamp in milliseconds to return logs after
        :type start_ts: int
        :param end_ts: timestamp in milliseconds to return logs before
        :type end_ts: int
        :return:
        :rtype: list
        """
        messages = []
        logger.debug('Getting events from CloudWatch Logs Group %s stream %s',
                     group_name, stream_name)
        paginator = self._logs.get_paginator('filter_log_events')
        resp_iter = paginator.paginate(
            logGroupName=group_name,
            logStreamNames=[stream_name],
            startTime=start_ts,
            endTime=end_ts
        )
        for resp in resp_iter:
            messages.extend(resp['events'])
        logger.debug('Found %d messages in stream %s',
                     len(messages), stream_name)
        return messages

    def get_cloudwatch_metric_sums(self, interval=86400, period=86400):
        """
        Return a dict of CloudWatch Metrics for this Lambda function, summed
        over ``interval``. Keys are metric names ("Errors", "Throttles",
        "Invocations") and values are sums of each ``period``-period datapoint,
        for the past ``interval`` seconds.

        For further information on these metrics, see:
        https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/
        lam-metricscollected.html

        :param interval: how many seconds of historical data to request
        :type interval: int
        :param period: the metric collection period to request from CloudWatch
        :type period: int
        :return: dict of metric name to sum for the last ``interval`` seconds
        :rtype: dict
        """
        res = {'Errors': 0.0, 'Throttles': 0.0, 'Invocations': 0.0}
        now = datetime.utcnow().replace(tzinfo=UTC())
        start = now - timedelta(seconds=interval)
        logger.debug('Checking CloudWatch Metrics for Lambda function: %s',
                     self._func_name)
        for m in self._cw.metrics.filter(
            Namespace='AWS/Lambda',
            Dimensions=[
                {
                    'Name': 'FunctionName',
                    'Value': self._func_name
                }
            ]
        ):
            dims = _name_value_dict(m.dimensions)
            # Lambda metrics are published twice, once with just
            # FunctionName, and a second time with both FunctionName and
            # Resource. Skip the duplicates that also have Resource dimension.
            if dims.keys() != ['FunctionName']:
                continue
            stats = m.get_statistics(
                Dimensions=[{'Name': 'FunctionName', 'Value': self._func_name}],
                StartTime=start,
                EndTime=now,
                Period=period,
                Statistics=['Sum']
            )
            val = sum([x['Sum'] for x in stats['Datapoints']])
            res[m.metric_name] = val
        logger.debug('Metrics for %s: %s', self._func_name, res)
        return res

    @staticmethod
    def find_matching_func_names(filter, region_name, client=None):
        """
        Return a list of all Lambda functions with names that either start
        with ``filter`` (if ``filter`` is a string) or match ``filter`` (if
        filter is a ``re.RegexObject``).

        :param filter: lambda function name filter
        :type filter: ``str`` ``re.RegexObject``
        :param region_name: region name to run against
        :type region_name: str
        :param client: boto3 Lambda client, or None to create new
        :type client: ``boto3.client``
        :return: list of matching Lambda function names
        :rtype: list
        """
        if client is None:
            client = boto3.client('lambda', region_name=region_name)
        if isinstance(filter, type('')):
            filter = re.compile('^' + re.escape(filter) + '.*')
        logger.debug(
            'Finding Lambda function names matching: %s', filter.pattern
        )
        matches = []
        total = 0
        paginator = client.get_paginator('list_functions')
        for response in paginator.paginate():
            for func in response['Functions']:
                total += 1
                if not filter.match(func['FunctionName']):
                    continue
                matches.append(func['FunctionName'])
        logger.debug('Matched %d of %d Lambda functions', len(matches), total)
        return sorted(matches)


class CustodianErrorReporter(object):
    """Scan and report on CW Metrics/Logs errors for c7n lambdas"""

    #: How far to look back in logs and metrics, in seconds
    INTERVAL = 86400

    #: Human-readable description of the interval
    INVL_DESC = 'day'

    #: What period to request CloudWatch metrics for
    METRIC_PERIOD = 86400

    #: Amount of time (float seconds) to sleep between checking each function,
    #: to try to avoid API rate limiting.
    INTER_FUNC_SLEEP = 3.0

    ALL_ERROR_FUNCTIONS = re.compile(r'^cloud-custodian.*')
    ALL_ERROR_LOG_RE = re.compile(r'.*(ERROR|WARNING).*')

    def __init__(self, config, region_name):
        """
        :param config: a non-region-specific config for this account
        :type config: CaisConfig
        :param region_name: the name of the region to run against
        :type region_name: str
        """
        self._config = config.config_for_region(region_name)
        self._region_name = region_name
        # override default max_attempts from 5 to 10, for throttling
        retry_conf = Config(retries={'max_attempts': BOTOCORE_MAX_ATTEMPTS})
        self._logs = boto3.client(
            'logs', config=retry_conf, region_name=region_name
        )
        self._cw = boto3.resource('cloudwatch', region_name=region_name)
        self._lambda = boto3.client('lambda', region_name=region_name)
        self._sqs = boto3.client('sqs', region_name=region_name)
        self._dlq_url = self._sqs_arn_to_url(
            self._config.dead_letter_queue_arn
        )
        self._now = datetime.now()
        self._start = self._now - timedelta(seconds=self.INTERVAL)
        self._failed_request_ids = {}  # set by _get_sqs_dlq()
        self._sqs_rcpts = []  # set by _get_sqs_dlq()

    def _sqs_arn_to_url(self, arn):
        """
        Find the URL for an SQS Queue given its ARN.

        :param arn: the ARN of the queue
        :type arn: str
        :return: the URL of the queue
        :rtype: str
        """
        m = re.match(r'^arn:aws:sqs:[^:]+:(\d+):([^:]+)$', arn)
        assert m is not None
        acct_id = m.group(1)
        queue_name = m.group(2)
        logger.debug(
            'Looking up SQS Queue URL for ARN %s (owner=%s name=%s)',
            arn, acct_id, queue_name
        )
        try:
            url = self._sqs.get_queue_url(
                QueueName=queue_name, QueueOwnerAWSAccountId=acct_id
            )['QueueUrl']
            logger.info('Found SQS Queue URL as %s for %s', url, arn)
            return url
        except self._sqs.exceptions.QueueDoesNotExist:
            logger.info('SQS Queue %s does not exist', arn)
            return None

    def run(self, never_match_re=None):
        """ collect and report on all cloud-custodian Lambda errors """
        print(
            'Searching cloud-custodian Lambda functions for failed invocations'
        )
        lambda_names = LambdaHealthChecker.find_matching_func_names(
            re.compile(r'^(custodian-|cloud-custodian-).*'), self._region_name
        )
        logger.debug('Custodian Lambda functions: %s', lambda_names)
        errors = False
        self._get_sqs_dlq()
        logger.debug(
            '%d failed Lambda invocations: %s',
            len(self._failed_request_ids), self._failed_request_ids.keys()
        )
        for fname in lambda_names:
            if not self._check_function(fname, never_match_re=never_match_re):
                logger.info(
                    '_check_function returned False (NOT HEALTHY) for: %s',
                    fname
                )
                errors = True
            logger.debug(
                'Sleeping %s seconds before checking next function',
                self.INTER_FUNC_SLEEP
            )
            sleep(self.INTER_FUNC_SLEEP)
        self._ack_sqs()
        req_ids = [
            i for i in self._failed_request_ids
            if self._failed_request_ids[i] is None
        ]
        if len(req_ids) > 0:
            print(
                "\n\n" +
                red('ERROR: %d failed Lambda RequestIDs could not be tied '
                    'to their function names: %s' % (len(req_ids), req_ids)) +
                "\n\n"
            )
        if errors:
            print('Some lambda functions had errors in the last '
                  '%s' % self.INVL_DESC)
            raise SystemExit(1)
        print('No Lambda functions had errors in the last ' + self.INVL_DESC)

    def _get_sqs_dlq(self):
        """
        Pull all messages from the SQS Dead Letter Queue. Add the failed Lambda
        RequestIDs to `self._failed_request_ids` and the SQS Reciept Handles
        to `self._sqs_rcpts`.
        """
        if self._dlq_url is None:
            logger.warning('Dead-letter SQS queue could not be found; skipping')
            return
        count = 0
        msgs = [None]
        logger.info('Polling SQS queue: %s', self._dlq_url)
        while len(msgs) > 0:
            response = self._sqs.receive_message(
                QueueUrl=self._dlq_url,
                WaitTimeSeconds=20,
                MaxNumberOfMessages=10,
                MessageAttributeNames=['RequestID', 'ErrorMessage'],
                AttributeNames=['SentTimestamp']
            )
            msgs = response.get('Messages', [])
            logger.debug('%d SQS Messages received from one poll', len(msgs))
            for m in msgs:
                count += 1
                self._failed_request_ids[
                    m['MessageAttributes']['RequestID']['StringValue']] = None
                self._sqs_rcpts.append(m['ReceiptHandle'])
        logger.info('Received %d SQS messages in total', count)
        logger.debug('SQS Message Receipt Handles: %s', self._sqs_rcpts)

    def _ack_sqs(self):
        """
        Delete (ack) all SQS messages in `self._sqs_rcpts`.
        """
        for rh in self._sqs_rcpts:
            self._sqs.delete_message(
                QueueUrl=self._dlq_url,
                ReceiptHandle=rh
            )

    def _check_function(self, func_name, never_match_re=None):
        """
        Check health of one Lambda function. Print information on it to STDOUT.
        Return True for healthy, False if errors/failures.

        :param func_name: Lambda function name to check
        :type func_name: str
        :param never_match_re: Regex for logs to NEVER return, even if they
          match ``always_match_re``.
        :type never_match_re: ``re``
        :return: whether the function had errors/failures
        :rtype: bool
        """
        c = LambdaHealthChecker(
            func_name, self._region_name, logs=self._logs, cw=self._cw
        )
        req_ids = [
            i for i in self._failed_request_ids
            if self._failed_request_ids[i] is None
        ]
        if self.ALL_ERROR_FUNCTIONS.match(func_name):
            logs = c.get_filtered_logs(
                req_ids, always_match_re=self.ALL_ERROR_LOG_RE,
                never_match_re=never_match_re
            )
        else:
            logs = c.get_filtered_logs(req_ids)
        metrics = c.get_cloudwatch_metric_sums()
        msg = []
        if metrics['Invocations'] > 0:
            throttle_pct = (metrics['Throttles'] / metrics['Invocations']) * 100
            error_pct = (metrics['Errors'] / metrics['Invocations']) * 100
        else:
            throttle_pct = 0
            error_pct = 0
        if error_pct > 50:
            msg.append('Lambda Function Errors: %s%% (%d of %d invocations)' % (
                error_pct,
                metrics['Errors'],
                metrics['Invocations']
            ))
        if throttle_pct > 50:
            msg.append(
                'Lambda Function Throttles: %s%% (%d of %d invocations)' % (
                    throttle_pct,
                    metrics['Throttles'],
                    metrics['Invocations']
                )
            )
        if len(logs) < 1 and len(msg) == 0:
            print(green('%s: OK\n' % func_name))
            return True
        print(red('%s: ERRORS' % func_name))
        for m in msg:
            print("\t%s" % red(m))
        if len(logs) < 1:
            return True
        print("\n\tLogs For Failed Invocations:\n")
        for req_id in logs.keys():
            if req_id == 'always_match':
                continue
            events = logs[req_id]
            self._failed_request_ids[req_id] = func_name
            print("\t" + red('RequestID=%s logGroupName=%s logStreamName=%s' % (
                req_id, events[0]['logGroupName'], events[0]['logStreamName']
            )))
            for e in events:
                print("\n".join([
                    "\t\t%s" % l.replace("\t", ' ')
                    for l in e['message'].split("\n")
                    if l.strip() != ''
                ]))
        if 'always_match' in logs:
            print("\t" + red(
                'Always-Match Logs (RequestID not in DLQ, but log matches '
                'regex that we want to always alarm on)'
            ))
            for e in logs['always_match']:
                print("\n".join([
                    "\t\t%s" % l.replace("\t", ' ')
                    for l in e['message'].split("\n")
                    if l.strip() != ''
                ]))
        print('')
        return False


def _name_value_dict(l):
    """
    Given a list (``l``) containing dicts with ``Name`` and ``Value`` keys,
    return a single dict of Name -> Value.
    """
    res = {}
    for item in l:
        res[item['Name']] = item['Value']
    return res


def parse_args(argv):
    p = argparse.ArgumentParser(
        description='Report on c7n lambda errors',
        epilog='This tool is part of manheim_c7n_tools v%s.\n'
               'For documentation, see: %s' % (VERSION, PROJECT_URL),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument('-V', '--version', action='version', version=VERSION)
    p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-A', '--no-assume-role', dest='assume_role',
                   action='store_false', default=True,
                   help='Do not assume a role, even if  specified in the '
                        'configuration file.')
    p.add_argument('-c', '--config', dest='config', action='store',
                   default='manheim-c7n-tools.yml',
                   help='Config file path (default: ./manheim-c7n-tools.yml)')
    p.add_argument('-n', '--never-match-re', dest='never_match_re', type=str,
                   action='store', default=None,
                   help='Regex for Lambda function logs to suppress/never '
                        'match')
    p.add_argument('ACCOUNT_NAME', action='store', type=str,
                   help='Account name to run errorscan against')
    p.add_argument('REGION_NAME', action='store', type=str,
                   help='AWS Region name to run errorscan against')
    args = p.parse_args(argv)
    return args


def main():
    args = parse_args(sys.argv[1:])

    # set logging level
    if args.verbose > 1:
        set_log_debug(logger)
    elif args.verbose == 1:
        set_log_info(logger)

    conf = ManheimConfig.from_file(args.config, args.ACCOUNT_NAME)
    if args.assume_role:
        assume_role(conf)
    if args.never_match_re is not None:
        args.never_match_re = re.compile(args.never_match_re)
    CustodianErrorReporter(conf, args.REGION_NAME).run(
        never_match_re=args.never_match_re
    )


if __name__ == "__main__":
    main()
