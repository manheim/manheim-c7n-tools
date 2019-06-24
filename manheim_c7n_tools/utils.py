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

import logging
import subprocess
import re
import os

import boto3

logger = logging.getLogger(__name__)


def set_log_info(log):
    """
    set log level to INFO with appropriate format

    :param log: the logger to set level and format on
    :type log: logging.Logger
    """
    set_log_level_format(log, logging.INFO,
                         '%(asctime)s %(levelname)s:%(name)s:%(message)s')


def set_log_debug(log):
    """
    set log level to DEBUG, and debug-level output format

    :param log: the logger to set level and format on
    :type log: logging.Logger
    """
    set_log_level_format(
        log,
        logging.DEBUG,
        "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
        "%(name)s.%(funcName)s() ] %(message)s"
    )


def set_log_level_format(log, level, format):
    """
    Set log level and format.

    :param log: the logger to set level and format on
    :type log: logging.Logger
    :param level: logging level; see the :py:mod:`logging` constants.
    :type level: int
    :param format: logging formatter format string
    :type format: str
    """
    formatter = logging.Formatter(fmt=format)
    log.handlers[0].setFormatter(formatter)
    log.setLevel(level)


def red(s):
    """
    Return the given string (``s``) surrounded by the ANSI escape codes to
    print it in red.
    :param s: string to console-color red
    :type s: str
    :returns: s surrounded by ANSI color escapes for red text
    :rtype: str
    """
    return "\033[0;31m" + s + "\033[0m"


def green(s):
    """
    Return the given string (``s``) surrounded by the ANSI escape codes to
    print it in green.
    :param s: string to console-color green
    :type s: str
    :returns: s surrounded by ANSI color escapes for green text
    :rtype: str
    """
    return "\033[0;32m" + s + "\033[0m"


def bold(s):
    """
    Return the given string (``s``) surrounded by the ANSI escape codes to
    print it in bold.
    :param s: string to console format as bold
    :type s: str
    :returns: s surrounded by ANSI color escapes for green text
    :rtype: str
    """
    return "\033[1m" + s + "\033[0m"


def git_html_url():
    """
    Run ``git config remote.origin.url`` in the current directory. Assuming it
    works, return the HTML URL for the repository (assumes github.com or
    github enterprise).

    :return: repository HTML base URL
    :rtype: str
    :raises: RuntimeError if the command fails or the URL cannot be parsed
    """
    p = subprocess.check_output(
        ['git', 'config', 'remote.origin.url'], text=True
    )
    p = p.strip()

    # git / ssh remote
    m = re.match(
        r'^([^@]+)@(?P<hostname>[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+):'
        r'(?P<path>.*/[^\.]*)(\.git)?$',
        p
    )
    if not m:
        m = re.match(
            r'^https?://(?P<hostname>[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+)/'
            r'(?P<path>.*/[^\.]*)(\.git)?$',
            p
        )
    if not m:
        raise RuntimeError(
            'Error: no pattern match for URL: %s' % p
        )
    return 'https://%s/%s/' % (m.group('hostname'), m.group('path'))


def assume_role(config):
    """
    Call sts:AssumeRole (via boto3) to assume the role specified by the
    configuration. Export the resulting credentials as environment variables
    for the current process.

    The configuration is taken from the ``assume_role`` section of the config.

    :param config: ManheimConfig object containing assume_role configuration
    :type config: ManheimConfig
    """
    try:
        conf = config.assume_role
    except AttributeError:
        logger.debug('No assume_role configuration; not assuming a role.')
        return
    kwargs = {
        'RoleArn': conf['role_arn'],
        'RoleSessionName': 'manheim-c7n-tools_%s' % config.account_name
    }
    if 'external_id' in conf:
        kwargs['ExternalId'] = conf['external_id']
    if 'duration_seconds' in conf:
        kwargs['DurationSeconds'] = int(conf['duration_seconds'])
    logger.info(
        'Calling sts:AssumeRole via boto3 with arguments: %s', kwargs
    )
    # We need to prevent STS from using the botocore/boto3 default session,
    # or else the default session will have the creds from the previous
    # account, not the assumed role, and none of this will work...
    sess = boto3.session.Session(region_name='us-east-1')
    sts = sess.client('sts')
    resp = sts.assume_role(**kwargs)
    os.environ['AWS_ACCESS_KEY_ID'] = resp['Credentials']['AccessKeyId']
    os.environ['AWS_SECRET_ACCESS_KEY'] = resp[
        'Credentials'
    ]['SecretAccessKey']
    os.environ['AWS_SESSION_TOKEN'] = resp['Credentials']['SessionToken']
    logger.info(
        'Exported AssumeRole credentials; AccessKeyId %s expires at %s; '
        'AssumedRoleUser ARN: %s', resp['Credentials']['AccessKeyId'],
        resp['Credentials']['Expiration'],
        resp['AssumedRoleUser']['Arn']
    )
