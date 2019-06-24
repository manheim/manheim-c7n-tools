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
import pytest
import os
from datetime import datetime

from manheim_c7n_tools.utils import (
    set_log_debug, set_log_info, set_log_level_format, red, green, bold,
    git_html_url, assume_role
)
from manheim_c7n_tools.config import ManheimConfig

from mock import patch, call, Mock, PropertyMock  # noqa

pbm = 'manheim_c7n_tools.utils'


class TestUtils(object):

    def test_set_log_info(self):
        mock_log = Mock(spec_set=logging.Logger)
        with patch('%s.set_log_level_format' % pbm, autospec=True) as mock_set:
            set_log_info(mock_log)
        assert mock_set.mock_calls == [
            call(
                mock_log, logging.INFO,
                '%(asctime)s %(levelname)s:%(name)s:%(message)s'
            )
        ]

    def test_set_log_debug(self):
        mock_log = Mock(spec_set=logging.Logger)
        with patch('%s.set_log_level_format' % pbm, autospec=True) as mock_set:
            set_log_debug(mock_log)
        assert mock_set.mock_calls == [
            call(mock_log, logging.DEBUG,
                 "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
                 "%(name)s.%(funcName)s() ] %(message)s")
        ]

    def test_set_log_level_format(self):
        mock_log = Mock(spec_set=logging.Logger)
        mock_handler = Mock(spec_set=logging.Handler)
        type(mock_log).handlers = [mock_handler]
        with patch(
            '%s.logging.Formatter' % pbm, autospec=True
        ) as mock_formatter:
            set_log_level_format(mock_log, 5, 'foo')
        assert mock_formatter.mock_calls == [
            call(fmt='foo')
        ]
        assert mock_handler.mock_calls == [
            call.setFormatter(mock_formatter.return_value)
        ]
        assert mock_log.mock_calls == [
            call.setLevel(5)
        ]

    def test_red(self):
        assert red('foo') == "\033[0;31mfoo\033[0m"

    def test_green(self):
        assert green('foo') == "\033[0;32mfoo\033[0m"

    def test_bold(self):
        assert bold('foo') == "\033[1mfoo\033[0m"


class TestGitHtmlUrl(object):

    def test_private_git(self):
        with patch(
            '%s.subprocess.check_output' % pbm, autospec=True
        ) as mock_co:
            mock_co.return_value = 'git@git.example.com:Foo/bar.git'
            res = git_html_url()
        assert res == 'https://git.example.com/Foo/bar/'
        assert mock_co.mock_calls == [
            call(['git', 'config', 'remote.origin.url'], text=True)
        ]

    def test_private_https(self):
        with patch(
            '%s.subprocess.check_output' % pbm, autospec=True
        ) as mock_co:
            mock_co.return_value = 'https://git.example.com/Foo/bar.git'
            res = git_html_url()
        assert res == 'https://git.example.com/Foo/bar/'
        assert mock_co.mock_calls == [
            call(['git', 'config', 'remote.origin.url'], text=True)
        ]

    def test_github_git(self):
        with patch(
            '%s.subprocess.check_output' % pbm, autospec=True
        ) as mock_co:
            mock_co.return_value = 'git@github.com:Foo/bar.git'
            res = git_html_url()
        assert res == 'https://github.com/Foo/bar/'
        assert mock_co.mock_calls == [
            call(['git', 'config', 'remote.origin.url'], text=True)
        ]

    def test_github_https(self):
        with patch(
            '%s.subprocess.check_output' % pbm, autospec=True
        ) as mock_co:
            mock_co.return_value = 'https://github.com/Foo/bar.git'
            res = git_html_url()
        assert res == 'https://github.com/Foo/bar/'
        assert mock_co.mock_calls == [
            call(['git', 'config', 'remote.origin.url'], text=True)
        ]

    def test_bad_pattern(self):
        with patch(
            '%s.subprocess.check_output' % pbm, autospec=True
        ) as mock_co:
            with pytest.raises(RuntimeError):
                mock_co.return_value = 'foobar'
                git_html_url()


class TestAssumeRole(object):

    def setup(self):
        self.m_conf = Mock(spec_set=ManheimConfig)
        type(self.m_conf).account_name = PropertyMock(return_value='aName')

    def test_success(self):
        m_sts = Mock()
        m_sts.assume_role.return_value = {
            'Credentials': {
                'AccessKeyId': 'AKID',
                'SecretAccessKey': 'SKey',
                'SessionToken': 'SToken',
                'Expiration': datetime(2018, 10, 8, 12, 13, 14)
            },
            'AssumedRoleUser': {
                'AssumedRoleId': 'ARid',
                'Arn': 'UserARN'
            },
            'PackedPolicySize': 123
        }
        m_sess = Mock()
        m_sess.client.return_value = m_sts
        type(self.m_conf).assume_role = PropertyMock(return_value={
            'role_arn': 'assumeRoleArn'
        })
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch.dict(os.environ, {}, clear=True):
                with patch('%s.boto3.session.Session' % pbm) as mock_boto:
                    mock_boto.return_value = m_sess
                    assume_role(self.m_conf)
                    assert os.environ == {
                        'AWS_ACCESS_KEY_ID': 'AKID',
                        'AWS_SECRET_ACCESS_KEY': 'SKey',
                        'AWS_SESSION_TOKEN': 'SToken'
                    }
        expected_args = {
            'RoleArn': 'assumeRoleArn',
            'RoleSessionName': 'manheim-c7n-tools_aName'
        }
        assert mock_boto.mock_calls == [
            call(region_name='us-east-1'),
            call().client('sts'),
            call().client().assume_role(**expected_args)
        ]
        assert mock_logger.mock_calls == [
            call.info(
                'Calling sts:AssumeRole via boto3 with arguments: %s',
                expected_args
            ),
            call.info(
                'Exported AssumeRole credentials; AccessKeyId %s expires at '
                '%s; AssumedRoleUser ARN: %s', 'AKID',
                datetime(2018, 10, 8, 12, 13, 14), 'UserARN'
            )
        ]

    def test_success_all_options(self):
        m_sts = Mock()
        m_sts.assume_role.return_value = {
            'Credentials': {
                'AccessKeyId': 'AKID',
                'SecretAccessKey': 'SKey',
                'SessionToken': 'SToken',
                'Expiration': datetime(2018, 10, 8, 12, 13, 14)
            },
            'AssumedRoleUser': {
                'AssumedRoleId': 'ARid',
                'Arn': 'UserARN'
            },
            'PackedPolicySize': 123
        }
        m_sess = Mock()
        m_sess.client.return_value = m_sts
        type(self.m_conf).assume_role = PropertyMock(return_value={
            'role_arn': 'assumeRoleArn',
            'external_id': 'eID',
            'duration_seconds': '1234'
        })
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch.dict(os.environ, {}, clear=True):
                with patch('%s.boto3.session.Session' % pbm) as mock_boto:
                    mock_boto.return_value = m_sess
                    assume_role(self.m_conf)
                    assert os.environ == {
                        'AWS_ACCESS_KEY_ID': 'AKID',
                        'AWS_SECRET_ACCESS_KEY': 'SKey',
                        'AWS_SESSION_TOKEN': 'SToken'
                    }
        expected_args = {
            'RoleArn': 'assumeRoleArn',
            'RoleSessionName': 'manheim-c7n-tools_aName',
            'ExternalId': 'eID',
            'DurationSeconds': 1234
        }
        assert mock_boto.mock_calls == [
            call(region_name='us-east-1'),
            call().client('sts'),
            call().client().assume_role(**expected_args)
        ]
        assert mock_logger.mock_calls == [
            call.info(
                'Calling sts:AssumeRole via boto3 with arguments: %s',
                expected_args
            ),
            call.info(
                'Exported AssumeRole credentials; AccessKeyId %s expires at '
                '%s; AssumedRoleUser ARN: %s', 'AKID',
                datetime(2018, 10, 8, 12, 13, 14), 'UserARN'
            )
        ]

    def test_no_role_arn(self):
        m_sts = Mock()
        m_sts.assume_role.return_value = {
            'Credentials': {
                'AccessKeyId': 'AKID',
                'SecretAccessKey': 'SKey',
                'SessionToken': 'SToken',
                'Expiration': datetime(2018, 10, 8, 12, 13, 14)
            },
            'AssumedRoleUser': {
                'AssumedRoleId': 'ARid',
                'Arn': 'UserARN'
            },
            'PackedPolicySize': 123
        }
        m_sess = Mock()
        m_sess.client.return_value = m_sts
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch.dict(os.environ, {}, clear=True):
                with patch('%s.boto3.session.Session' % pbm) as mock_boto:
                    mock_boto.return_value = m_sess
                    assume_role(self.m_conf)
                    assert os.environ == {}
        assert mock_boto.mock_calls == []
        assert mock_logger.mock_calls == [
            call.debug('No assume_role configuration; not assuming a role.')
        ]
