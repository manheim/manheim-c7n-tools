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

from mock import patch, call, Mock, mock_open
import pytest
import yaml

from manheim_c7n_tools.config import ManheimConfig, MANHEIM_CONFIG_SCHEMA

pbm = 'manheim_c7n_tools.config'


class TestManheimConfig(object):

    def test_init(self):
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch(
                '%s.jsonschema.validate' % pbm, autospec=True
            ) as mock_validate:
                cls = ManheimConfig(
                    foo='bar', baz=2, regions=['us-east-1'],
                    config_path='manheim-c7n-tools.yml', account_id='1234',
                    cleanup_notify=['foo@bar.com']
                )
        assert cls._config == {
            'foo': 'bar', 'baz': 2, 'regions': ['us-east-1'],
            'account_id': '1234', 'cleanup_notify': ['foo@bar.com']
        }
        assert cls.config_path == 'manheim-c7n-tools.yml'
        assert mock_logger.mock_calls == [
            call.debug('Validating configuration...')
        ]
        assert mock_validate.mock_calls == [
            call(
                {
                    'foo': 'bar', 'baz': 2, 'regions': ['us-east-1'],
                    'account_id': '1234', 'cleanup_notify': ['foo@bar.com']
                },
                MANHEIM_CONFIG_SCHEMA
            )
        ]

    def test_init_not_us_east_1(self):
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch(
                '%s.jsonschema.validate' % pbm, autospec=True
            ) as mock_validate:
                cls = ManheimConfig(
                    foo='bar', baz=2, regions=['us-east-2'],
                    config_path='manheim-c7n-tools.yml', account_id='1234',
                    cleanup_notify=['foo@bar.com']
                )
        assert cls._config == {
            'foo': 'bar', 'baz': 2, 'regions': ['us-east-2'],
            'account_id': '1234', 'cleanup_notify': ['foo@bar.com']
        }
        assert cls.config_path == 'manheim-c7n-tools.yml'
        assert mock_logger.mock_calls == [
            call.debug('Validating configuration...')
        ]
        assert mock_validate.mock_calls == [
            call(
                {
                    'foo': 'bar', 'baz': 2, 'regions': ['us-east-2'],
                    'account_id': '1234', 'cleanup_notify': ['foo@bar.com']
                },
                MANHEIM_CONFIG_SCHEMA
            )
        ]

    def test_getattr(self):
        with patch('%s.logger' % pbm, autospec=True):
            with patch('%s.jsonschema.validate' % pbm, autospec=True):
                cls = ManheimConfig(
                    foo='bar', baz=2, regions=['us-east-1'], config_path='foo',
                    account_id='012345'
                )
        assert cls.foo == 'bar'
        assert cls.baz == 2
        assert cls.config_path == 'foo'
        assert cls.account_id == '012345'
        with pytest.raises(AttributeError):
            cls.missingAttr

    def test_from_file(self):
        m_conf = Mock()
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch(
                '%s.open' % pbm, mock_open(read_data='foo'), create=True
            ) as m_open:
                with patch('%s.yaml.load' % pbm, autospec=True) as mock_load:
                    with patch(
                        '%s.ManheimConfig' % pbm, autospec=True
                    ) as mock_conf:
                        mock_conf.return_value = m_conf
                        mock_load.return_value = [
                            {
                                'account_name': 'a1',
                                'foo': 'bar',
                                'baz': 2,
                                'regions': ['us-east-1']
                            },
                            {
                                'account_name': 'a2',
                                'foo': 'bar1',
                                'baz': 4,
                                'regions': ['us-east-2']
                            }
                        ]
                        res = ManheimConfig.from_file('/tmp/conf.yml', 'a2')
        assert res == m_conf
        assert mock_logger.mock_calls == [
            call.info('Loading config from: %s', '/tmp/conf.yml')
        ]
        assert m_open.mock_calls == [
            call('/tmp/conf.yml', 'r'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None)
        ]
        assert mock_load.mock_calls == [
            call('foo', Loader=yaml.SafeLoader)
        ]
        assert mock_conf.mock_calls == [
            call(
                account_name='a2', foo='bar1', baz=4, regions=['us-east-2'],
                config_path='/tmp/conf.yml'
            )
        ]

    def test_from_file_name_missing(self):
        m_conf = Mock()
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch(
                '%s.open' % pbm, mock_open(read_data='foo'), create=True
            ) as m_open:
                with patch('%s.yaml.load' % pbm, autospec=True) as mock_load:
                    with patch(
                        '%s.ManheimConfig' % pbm, autospec=True
                    ) as mock_conf:
                        mock_conf.return_value = m_conf
                        mock_load.return_value = [
                            {
                                'account_name': 'a1',
                                'foo': 'bar',
                                'baz': 2,
                                'regions': ['us-east-1']
                            },
                            {
                                'account_name': 'a2',
                                'foo': 'bar1',
                                'baz': 4,
                                'regions': ['us-east-2']
                            }
                        ]
                        with pytest.raises(RuntimeError) as exc:
                            ManheimConfig.from_file('/tmp/conf.yml', 'BAD')
        assert str(exc.value) == 'ERROR: No account with name "BAD"' \
                                 ' in /tmp/conf.yml'
        assert mock_logger.mock_calls == [
            call.info('Loading config from: %s', '/tmp/conf.yml')
        ]
        assert m_open.mock_calls == [
            call('/tmp/conf.yml', 'r'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None)
        ]
        assert mock_load.mock_calls == [
            call('foo', Loader=yaml.SafeLoader)
        ]
        assert mock_conf.mock_calls == []

    def test_list_accounts(self):
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch(
                '%s.open' % pbm, mock_open(read_data='foo'), create=True
            ) as m_open:
                with patch('%s.yaml.load' % pbm, autospec=True) as mock_load:
                    with patch(
                        '%s.ManheimConfig' % pbm, autospec=True
                    ) as mock_conf:
                        mock_load.return_value = [
                            {
                                'account_name': 'a1',
                                'account_id': '1111',
                                'foo': 'bar',
                                'baz': 2,
                                'regions': ['us-east-1']
                            },
                            {
                                'account_name': 'a2',
                                'account_id': 2222,
                                'foo': 'bar1',
                                'baz': 4,
                                'regions': ['us-east-2']
                            }
                        ]
                        res = ManheimConfig.list_accounts('/tmp/conf.yml')
        assert res == {'a1': '1111', 'a2': '2222'}
        assert mock_logger.mock_calls == [
            call.info('Loading config from: %s', '/tmp/conf.yml')
        ]
        assert m_open.mock_calls == [
            call('/tmp/conf.yml', 'r'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None)
        ]
        assert mock_load.mock_calls == [
            call('foo', Loader=yaml.SafeLoader)
        ]
        assert mock_conf.mock_calls == []

    def test_config_for_region(self):
        original = {
            'foo': 'bar%%AWS_REGION%%baz',
            'bar': [
                'baz',
                'AWS_REGION',
                '%%AWS_REGION%%',
                'xx%%AWS_REGION%%xx',
                'blam',
                'xx%%POLICYGEN_ENV_foo%%xx'
            ],
            'baz': {
                'blam': {
                    'blarg%%AWS_REGION%%xx': 'xxx%%AWS_REGION%%xxx'
                }
            },
            'regions': ['us-east-1', 'us-east-2'],
            'account_id': '012345',
            'config_path': '/tmp/baz.yml'
        }
        expected = {
            'foo': 'barus-east-2baz',
            'bar': [
                'baz',
                'AWS_REGION',
                'us-east-2',
                'xxus-east-2xx',
                'blam',
                'xxbarVARxx'
            ],
            'baz': {
                'blam': {
                    'blargus-east-2xx': 'xxxus-east-2xxx'
                }
            },
            'account_id': '012345',
            'regions': ['us-east-1', 'us-east-2'],
            'cleanup_notify': []
        }
        with patch('%s.jsonschema.validate' % pbm, autospec=True):
            with patch.dict(
                'os.environ',
                {'foo': 'bar', 'POLICYGEN_ENV_foo': 'barVAR'},
                clear=True
            ):
                conf = ManheimConfig(**original)
                result = conf.config_for_region('us-east-2')
        assert result._config == expected
        assert result.config_path == '/tmp/baz.yml'
