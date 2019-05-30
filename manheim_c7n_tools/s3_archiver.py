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
Script to clean up the custodian S3 buckets, by moving logs from any deleted
policies to an "archived-logs/" prefix.
"""

import sys
import logging
import boto3
import argparse

import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

from manheim_c7n_tools.utils import set_log_info, set_log_debug
from manheim_c7n_tools.version import VERSION

logger = logging.getLogger(__name__)


class S3Archiver(object):

    def __init__(self, region_name, bucket_name, conf_file, dryrun=False):
        logger.info('Connecting to S3 in %s for bucket %s (config file: %s)',
                    region_name, bucket_name, conf_file)
        self._s3 = boto3.resource('s3', region_name=region_name)
        self._region_name = region_name
        self._bucket_name = bucket_name
        self._bucket = self._s3.Bucket(bucket_name)
        self._conf_file = conf_file
        self._dryrun = dryrun

    def run(self):
        policy_names = self._get_policy_names()
        logger.debug('Found %d policies in config', len(policy_names))
        prefixes = self._get_s3_policy_prefixes()
        logger.debug('Found %d policy prefixes in S3 bucket', len(prefixes))
        move_count = 0
        for p in prefixes:
            if p not in policy_names:
                self._move_prefix(p)
                move_count += 1
        logger.info('Archived %d policy name prefixes', move_count)

    def _move_prefix(self, policy_name):
        """
        Given a policy name key prefix in S3, move everything under it to the
        ``archived-logs/`` prefix.

        :param policy_name: name of the policy prefix in S3
        :type policy_name: str
        """
        if not self._dryrun:
            logger.info('Moving policy prefix logs/%s to archived-logs/%s',
                        policy_name, policy_name)
        count = 0
        for o in self._bucket.objects.filter(
            Prefix='logs/%s/' % policy_name
        ):
            dest = o.key.replace('logs/', 'archived-logs/')
            self._s3_move_file(o, dest)
            count += 1
        if self._dryrun:
            logger.info('DRYRUN: Would move %d objects under logs/%s to '
                        'archived-logs/%s', count, policy_name, policy_name)
        else:
            logger.info('Moved %d objects under logs/%s to archived-logs/%s',
                        count, policy_name, policy_name)

    def _s3_move_file(self, obj_summary, dest_key):
        """
        S3 doesn't have any built-in logic for "moving" or "renaming" an object.
        The way `awscli` and all of the SDK examples do this is by copying the
        source to the destination, then deleting the source. To make this a bit
        more unweildy, it's far easier to copy with the boto3 client than with
        the fancy Resource-oriented API.

        :param obj_summary: the S3 ObjectSummary instance to move
        :type obj_summary: ``boto3.S3.ObjectSummary``
        :param dest_key: S3 key to move to
        :type dest_key: str
        """
        if self._dryrun:
            logger.debug('DRYRUN: Would move %s to %s',
                         obj_summary.key, dest_key)
            return
        # ELSE not a dry run, actually do it
        client = self._bucket.meta.client
        logger.debug('Copying %s to %s', obj_summary.key, dest_key)
        client.copy_object(
            ACL='private',
            Bucket=self._bucket.name,
            Key=dest_key,
            CopySource={
                'Bucket': self._bucket.name,
                'Key': obj_summary.key
            },
            MetadataDirective='COPY',
            TaggingDirective='COPY'
        )
        # ok, copied, now delete
        logger.debug('Deleting %s', obj_summary.key)
        obj_summary.delete()

    def _get_s3_policy_prefixes(self):
        """
        Find all of the per-policy prefixes (a.k.a. "directories") in the S3
        bucket. Return a list of them

        :return: list of per-policy prefixes in S3 bucket
        :rtype: list
        """
        client = self._bucket.meta.client
        response = client.list_objects(
            Bucket=self._bucket.name,
            Delimiter='/',
            Prefix='logs/'
        )
        if response['IsTruncated']:
            raise RuntimeError('ERROR: S3 response was truncated!')
        result = []
        for pname in response.get('CommonPrefixes', []):
            result.append(pname['Prefix'].replace('logs/', '').strip('/'))
        return result

    def _get_policy_names(self):
        """
        Read the custodian config file; return a list of policy names.

        :return: list of policy names
        :rtype: list
        """
        with open(self._conf_file, 'r') as fh:
            contents = fh.read()
        data = yaml.load(contents, Loader=SafeLoader)
        return [p['name'] for p in data['policies']]


def parse_args(argv):
    p = argparse.ArgumentParser(
        description='Archive S3 logs for deleted policies'
    )
    p.add_argument('-V', '--version', action='version', version=VERSION)
    p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-d', '--dry-run', dest='dryrun', action='store_true',
                   default=False,
                   help='print what would be done; dont move anything')
    p.add_argument('REGION_NAME', action='store', type=str,
                   help='AWS region name to run against')
    p.add_argument('BUCKET_NAME', action='store', type=str,
                   help='S3 Bucket Name')
    p.add_argument('CONF_FILE', action='store', type=str,
                   help='path to cloud-custodian config YML file')
    args = p.parse_args(argv)
    return args


def main():
    # setup logging for direct command-line use
    global logger
    FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
    logging.basicConfig(level=logging.INFO, format=FORMAT)
    logger = logging.getLogger()

    # suppress boto3 internal logging below WARNING level
    boto3_log = logging.getLogger("boto3")
    boto3_log.setLevel(logging.WARNING)
    boto3_log.propagate = True

    # suppress botocore internal logging below WARNING level
    botocore_log = logging.getLogger("botocore")
    botocore_log.setLevel(logging.WARNING)
    botocore_log.propagate = True
    # end setup logging
    args = parse_args(sys.argv[1:])

    # set logging level
    if args.verbose > 1:
        set_log_debug(logger)
    elif args.verbose == 1:
        set_log_info(logger)

    S3Archiver(
        args.REGION_NAME, args.BUCKET_NAME, args.CONF_FILE, dryrun=args.dryrun
    ).run()


if __name__ == "__main__":
    main()
