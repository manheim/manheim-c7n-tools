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

import sys
from mock import patch, call, DEFAULT, Mock, PropertyMock
import pytest
from functools import partial

from c7n.config import Config
from c7n_mailer.cli import CONFIG_SCHEMA as MAILER_SCHEMA

from manheim_c7n_tools.vendor.mugc import AWS
import manheim_c7n_tools.runner as runner
from manheim_c7n_tools.runner import BaseStep
from manheim_c7n_tools.utils import bold
from manheim_c7n_tools.config import ManheimConfig
from c7n_mailer.deploy import get_archive
from c7n.mu import PythonPackageArchive

pbm = 'manheim_c7n_tools.runner'


ALL_REGIONS = [
    "ap-south-1",
    "eu-west-3",
    "eu-west-2",
    "eu-west-1",
    "ap-northeast-2",
    "ap-northeast-1",
    "sa-east-1",
    "ca-central-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "eu-central-1",
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2"
]


class FakeConfig:

    def __init__(self, regions):
        self.regions = regions


class StepTester(object):

    def setup(self):
        # in order to supplant __getattr__ calls
        self.m_conf = Mock(spec=ManheimConfig)
        self.m_conf.account_id = '01234567890'


class TestPolicygenStep(StepTester):

    def test_run(self):
        with patch('%s.PolicyGen' % pbm, autospec=True) as mock_pg:
            runner.PolicygenStep(None, self.m_conf).run()
        assert mock_pg.mock_calls == [
            call(self.m_conf),
            call().run()
        ]

    def test_dryrun(self):
        with patch('%s.PolicyGen' % pbm, autospec=True) as mock_pg:
            runner.PolicygenStep(None, self.m_conf).dryrun()
        assert mock_pg.mock_calls == [
            call(self.m_conf),
            call().run()
        ]

    def test_run_in_region(self):
        conf = FakeConfig(ALL_REGIONS)
        for rname in ALL_REGIONS:
            if rname == ALL_REGIONS[0]:
                assert runner.PolicygenStep.run_in_region(rname, conf) is True
            else:
                assert runner.PolicygenStep.run_in_region(rname, conf) is False


class TestValidateStep(StepTester):

    def test_run(self):
        mock_conf = Mock(spec_set=ManheimConfig)
        with patch('%s.validate' % pbm, autospec=True) as mock_validate:
            with patch('%s.Config.empty' % pbm) as mock_empty:
                mock_empty.return_value = mock_conf
                runner.ValidateStep('rName', self.m_conf).run()
        assert mock_validate.mock_calls == [call(mock_conf)]
        assert mock_empty.mock_calls == [
            call(configs=['custodian_rName.yml'], region='rName')
        ]

    def test_dryrun(self):
        mock_conf = Mock(spec_set=ManheimConfig)
        with patch('%s.validate' % pbm, autospec=True) as mock_validate:
            with patch('%s.Config.empty' % pbm) as mock_empty:
                mock_empty.return_value = mock_conf
                runner.ValidateStep('rName', self.m_conf).dryrun()
        assert mock_validate.mock_calls == [call(mock_conf)]
        assert mock_empty.mock_calls == [
            call(configs=['custodian_rName.yml'], region='rName')
        ]

    def test_run_in_region(self):
        for rname in ALL_REGIONS:
            assert runner.ValidateStep.run_in_region(rname, None) is True


class TestMugcStep(StepTester):

    def test_run(self):
        mock_pol1 = Mock(provider_name='foo')
        mock_pol2 = Mock(provider_name='aws')
        mock_pol3 = Mock(provider_name='azure')
        mock_conf = Mock(spec_set=ManheimConfig)
        mock_aws = Mock(spec_set=AWS)
        mock_aws.initialize_policies.return_value = {'aws': 'policies'}
        mock_pc = Mock()
        with patch('%s.Config.empty' % pbm) as mock_empty:
            mock_empty.return_value = mock_conf
            with patch.multiple(
                pbm,
                AWS=DEFAULT,
                load_policies=DEFAULT,
                resources_gc_prefix=DEFAULT,
                PolicyCollection=DEFAULT
            ) as mocks:
                mocks['AWS'].return_value = mock_aws
                mocks['PolicyCollection'].return_value = mock_pc
                mocks['load_policies'].return_value = [
                    mock_pol1, mock_pol2, mock_pol3
                ]
                runner.MugcStep('rName', self.m_conf).run()
        assert mock_empty.mock_calls == [
            call(
                config_files=['custodian_rName.yml'],
                regions=['rName'],
                prefix='custodian-',
                policy_regex='^custodian-.*',
                assume=None,
                policy_filter=None,
                log_group=None,
                external_id=None,
                cache_period=0,
                cache=None,
                present=False
            )
        ]
        assert mocks['load_policies'].mock_calls == [
            call(mock_conf, mock_conf)
        ]
        assert mocks['PolicyCollection'].mock_calls == [
            call([mock_pol2], mock_conf)
        ]
        assert mocks['AWS'].mock_calls == [
            call(),
            call().initialize_policies(mock_pc, mock_conf)
        ]
        assert mocks['resources_gc_prefix'].mock_calls == [
            call(mock_conf, mock_conf, {'aws': 'policies'})
        ]

    def test_dryrun(self):
        mock_pol1 = Mock(provider_name='foo')
        mock_pol2 = Mock(provider_name='aws')
        mock_pol3 = Mock(provider_name='azure')
        mock_conf = Mock(spec_set=ManheimConfig)
        mock_aws = Mock(spec_set=AWS)
        mock_aws.initialize_policies.return_value = {'aws': 'policies'}
        mock_pc = Mock()
        with patch('%s.Config.empty' % pbm) as mock_empty:
            mock_empty.return_value = mock_conf
            with patch.multiple(
                pbm,
                AWS=DEFAULT,
                load_policies=DEFAULT,
                resources_gc_prefix=DEFAULT,
                PolicyCollection=DEFAULT
            ) as mocks:
                mocks['AWS'].return_value = mock_aws
                mocks['PolicyCollection'].return_value = mock_pc
                mocks['load_policies'].return_value = [
                    mock_pol1, mock_pol2, mock_pol3
                ]
                runner.MugcStep('rName', self.m_conf).dryrun()
        assert mock_empty.mock_calls == [
            call(
                config_files=['custodian_rName.yml'],
                regions=['rName'],
                prefix='custodian-',
                policy_regex='^custodian-.*',
                assume=None,
                policy_filter=None,
                log_group=None,
                external_id=None,
                cache_period=0,
                cache=None,
                present=False,
                dryrun=True
            )
        ]
        assert mocks['load_policies'].mock_calls == [
            call(mock_conf, mock_conf)
        ]
        assert mocks['PolicyCollection'].mock_calls == [
            call([mock_pol2], mock_conf)
        ]
        assert mocks['AWS'].mock_calls == [
            call(),
            call().initialize_policies(mock_pc, mock_conf)
        ]
        assert mocks['resources_gc_prefix'].mock_calls == [
            call(mock_conf, mock_conf, {'aws': 'policies'})
        ]

    def test_run_in_region(self):
        for rname in ALL_REGIONS:
            assert runner.MugcStep.run_in_region(rname, None) is True


class TestCustodianStep(StepTester):

    def test_run(self):
        type(self.m_conf).output_s3_bucket_name = PropertyMock(
            return_value='cloud-custodian-ACCT-REGION'
        )
        type(self.m_conf).custodian_log_group = PropertyMock(
            return_value='/cloud-custodian/ACCT/REGION'
        )
        mock_conf = Mock(spec_set=Config)
        with patch('%s.run' % pbm) as mock_run:
            with patch('%s.Config.empty' % pbm) as mock_empty:
                mock_empty.return_value = mock_conf
                runner.CustodianStep('rName', self.m_conf).run()
        assert mock_run.mock_calls == [call(mock_conf)]
        assert mock_empty.mock_calls == [
            call(
                configs=['custodian_rName.yml'],
                region='rName',
                regions=['rName'],
                log_group='/cloud-custodian/ACCT/REGION',
                verbose=1,
                metrics_enabled=True,
                subparser='run',
                cache='/tmp/.cache/cloud-custodian.cache',
                command='c7n.commands.run',
                output_dir='cloud-custodian-ACCT-REGION/logs',
                vars=None,
                dryrun=False
            )
        ]

    def test_dryrun(self):
        type(self.m_conf).output_s3_bucket_name = PropertyMock(
            return_value='cloud-custodian-ACCT-REGION'
        )
        type(self.m_conf).custodian_log_group = PropertyMock(
            return_value='/cloud-custodian/ACCT/REGION'
        )
        mock_conf = Mock(spec_set=Config)
        with patch('%s.run' % pbm) as mock_run:
            with patch('%s.Config.empty' % pbm) as mock_empty:
                mock_empty.return_value = mock_conf
                runner.CustodianStep('rName', self.m_conf).dryrun()
        assert mock_run.mock_calls == [call(mock_conf)]
        assert mock_empty.mock_calls == [
            call(
                configs=['custodian_rName.yml'],
                region='rName',
                regions=['rName'],
                verbose=1,
                metrics_enabled=False,
                subparser='run',
                cache='/tmp/.cache/cloud-custodian.cache',
                command='c7n.commands.run',
                output_dir='dryrun/rName',
                vars=None,
                dryrun=True
            )
        ]

    def test_run_in_region(self):
        for rname in ALL_REGIONS:
            assert runner.CustodianStep.run_in_region(rname, None) is True


class TestMailerStep(StepTester):

    @patch(f'{pbm}.__file__', 'path/to/runner.py')
    def test_mailer_config_docker(self):
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_conf).mailer_config = PropertyMock(
            return_value={'mailer': 'config'}
        )

        def se_mailer_setup_defaults(d):
            d['defaults'] = 'set'

        def se_isdir(d):
            if d == '/manheim_c7n_tools/manheim_c7n_tools/mailer-templates':
                return True
            return False

        def se_abspath(p):
            return f'/abspath/{p}'

        with patch(
            '%s.jsonschema.validate' % pbm, autospec=True
        ) as mock_validate:
            with patch(
                '%s.mailer_setup_defaults' % pbm, autospec=True
            ) as mock_msd:
                mock_msd.side_effect = se_mailer_setup_defaults
                with patch(
                    '%s.os.path.isdir' % pbm
                ) as mock_isdir:
                    mock_isdir.side_effect = se_isdir
                    with patch(
                        '%s.os.path.abspath' % pbm
                    ) as mock_abspath:
                        mock_abspath.side_effect = se_abspath
                        res = runner.MailerStep(
                            'rName', m_conf
                        ).mailer_config
        expected = {
            'mailer': 'config',
            'defaults': 'set',
            'templates_folders': [
                '/manheim_c7n_tools/manheim_c7n_tools/mailer-templates'
            ]
        }
        assert res == expected
        assert mock_validate.mock_calls == [
            call(expected, MAILER_SCHEMA)
        ]
        assert mock_msd.mock_calls == [
            call(expected)
        ]

    @patch(f'{pbm}.__file__', 'path/to/runner.py')
    def test_mailer_config_nondocker(self):
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_conf).mailer_config = PropertyMock(
            return_value={'mailer': 'config'}
        )

        def se_mailer_setup_defaults(d):
            d['defaults'] = 'set'
            d['templates_folders'] = []

        def se_isdir(d):
            if d == '/abspath/path/to/mailer-templates':
                return True
            return False

        def se_abspath(p):
            return f'/abspath/{p}'

        with patch(
            '%s.jsonschema.validate' % pbm, autospec=True
        ) as mock_validate:
            with patch(
                '%s.mailer_setup_defaults' % pbm, autospec=True
            ) as mock_msd:
                mock_msd.side_effect = se_mailer_setup_defaults
                with patch(
                    '%s.os.path.isdir' % pbm
                ) as mock_isdir:
                    mock_isdir.side_effect = se_isdir
                    with patch(
                        '%s.os.path.abspath' % pbm
                    ) as mock_abspath:
                        mock_abspath.side_effect = se_abspath
                        res = runner.MailerStep(
                            'rName', m_conf
                        ).mailer_config
        expected = {
            'mailer': 'config',
            'defaults': 'set',
            'templates_folders': ['/abspath/path/to/mailer-templates']
        }
        assert res == expected
        assert mock_validate.mock_calls == [
            call(expected, MAILER_SCHEMA)
        ]
        assert mock_msd.mock_calls == [
            call(expected)
        ]

    @patch(f'{pbm}.__file__', 'path/to/runner.py')
    def test_mailer_config_existing_folders(self):
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_conf).mailer_config = PropertyMock(
            return_value={'mailer': 'config'}
        )

        def se_mailer_setup_defaults(d):
            d['defaults'] = 'set'
            d['templates_folders'] = ['/my/folder']

        def se_isdir(d):
            if d == '/abspath/path/to/mailer-templates':
                return True
            return False

        def se_abspath(p):
            return f'/abspath/{p}'

        with patch(
            '%s.jsonschema.validate' % pbm, autospec=True
        ) as mock_validate:
            with patch(
                '%s.mailer_setup_defaults' % pbm, autospec=True
            ) as mock_msd:
                mock_msd.side_effect = se_mailer_setup_defaults
                with patch(
                    '%s.os.path.isdir' % pbm
                ) as mock_isdir:
                    mock_isdir.side_effect = se_isdir
                    with patch(
                        '%s.os.path.abspath' % pbm
                    ) as mock_abspath:
                        mock_abspath.side_effect = se_abspath
                        res = runner.MailerStep(
                            'rName', m_conf
                        ).mailer_config
        expected = {
            'mailer': 'config',
            'defaults': 'set',
            'templates_folders': [
                '/abspath/path/to/mailer-templates',
                '/my/folder'
            ]
        }
        assert res == expected
        assert mock_validate.mock_calls == [
            call(expected, MAILER_SCHEMA)
        ]
        assert mock_msd.mock_calls == [
            call(expected)
        ]

    @patch(f'{pbm}.__file__', 'path/to/runner.py')
    def test_mailer_config_only_existing(self):
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_conf).mailer_config = PropertyMock(
            return_value={'mailer': 'config'}
        )

        def se_mailer_setup_defaults(d):
            d['defaults'] = 'set'
            d['templates_folders'] = ['/my/folder']

        def se_isdir(d):
            return False

        def se_abspath(p):
            return f'/abspath/{p}'

        with patch(
            '%s.jsonschema.validate' % pbm, autospec=True
        ) as mock_validate:
            with patch(
                '%s.mailer_setup_defaults' % pbm, autospec=True
            ) as mock_msd:
                mock_msd.side_effect = se_mailer_setup_defaults
                with patch(
                    '%s.os.path.isdir' % pbm
                ) as mock_isdir:
                    mock_isdir.side_effect = se_isdir
                    with patch(
                        '%s.os.path.abspath' % pbm
                    ) as mock_abspath:
                        mock_abspath.side_effect = se_abspath
                        res = runner.MailerStep(
                            'rName', m_conf
                        ).mailer_config
        expected = {
            'mailer': 'config',
            'defaults': 'set',
            'templates_folders': [
                '/my/folder'
            ]
        }
        assert res == expected
        assert mock_validate.mock_calls == [
            call(expected, MAILER_SCHEMA)
        ]
        assert mock_msd.mock_calls == [
            call(expected)
        ]

    @patch(f'{pbm}.__file__', 'path/to/runner.py')
    def test_mailer_config_pwd(self):
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_conf).mailer_config = PropertyMock(
            return_value={'mailer': 'config'}
        )

        def se_mailer_setup_defaults(d):
            d['defaults'] = 'set'

        def se_isdir(d):
            if d == '/abspath/./mailer-templates':
                return True
            return False

        def se_abspath(p):
            return f'/abspath/{p}'

        with patch(
            '%s.jsonschema.validate' % pbm, autospec=True
        ) as mock_validate:
            with patch(
                '%s.mailer_setup_defaults' % pbm, autospec=True
            ) as mock_msd:
                mock_msd.side_effect = se_mailer_setup_defaults
                with patch(
                    '%s.os.path.isdir' % pbm
                ) as mock_isdir:
                    mock_isdir.side_effect = se_isdir
                    with patch(
                        '%s.os.path.abspath' % pbm
                    ) as mock_abspath:
                        mock_abspath.side_effect = se_abspath
                        res = runner.MailerStep(
                            'rName', m_conf
                        ).mailer_config
        expected = {
            'mailer': 'config',
            'defaults': 'set',
            'templates_folders': [
                '/abspath/./mailer-templates'
            ]
        }
        assert res == expected
        assert mock_validate.mock_calls == [
            call(expected, MAILER_SCHEMA)
        ]
        assert mock_msd.mock_calls == [
            call(expected)
        ]

    @patch(f'{pbm}.__file__', 'path/to/runner.py')
    def test_mailer_config_all_exist(self):
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_conf).mailer_config = PropertyMock(
            return_value={'mailer': 'config'}
        )

        def se_mailer_setup_defaults(d):
            d['defaults'] = 'set'
            d['templates_folders'] = ['/my/folder']

        def se_isdir(d):
            return True

        def se_abspath(p):
            return f'/abspath/{p}'

        with patch(
            '%s.jsonschema.validate' % pbm, autospec=True
        ) as mock_validate:
            with patch(
                '%s.mailer_setup_defaults' % pbm, autospec=True
            ) as mock_msd:
                mock_msd.side_effect = se_mailer_setup_defaults
                with patch(
                    '%s.os.path.isdir' % pbm
                ) as mock_isdir:
                    mock_isdir.side_effect = se_isdir
                    with patch(
                        '%s.os.path.abspath' % pbm
                    ) as mock_abspath:
                        mock_abspath.side_effect = se_abspath
                        res = runner.MailerStep(
                            'rName', m_conf
                        ).mailer_config
        expected = {
            'mailer': 'config',
            'defaults': 'set',
            'templates_folders': [
                '/abspath/path/to/mailer-templates',
                '/manheim_c7n_tools/manheim_c7n_tools/mailer-templates',
                '/abspath/./mailer-templates',
                '/my/folder'
            ]
        }
        assert res == expected
        assert mock_validate.mock_calls == [
            call(expected, MAILER_SCHEMA)
        ]
        assert mock_msd.mock_calls == [
            call(expected)
        ]

    def test_run(self):
        m_partial = Mock(spec_set=partial)
        m_conf = Mock(spec_set=ManheimConfig)
        with patch(
            '%s.MailerStep.mailer_config' % pbm, new_callable=PropertyMock
        ) as mock_config:
            with patch(
                '%s.mailer_deploy.provision' % pbm, autospec=True
            ) as mock_prov:
                with patch(
                    '%s.functools.partial' % pbm, autospec=True
                ) as mock_partial:
                    with patch(
                        '%s.session_factory' % pbm, autospec=True
                    ) as mock_sf:
                        mock_config.return_value = m_conf
                        mock_partial.return_value = m_partial
                        runner.MailerStep('rName', self.m_conf).run()
        assert mock_partial.mock_calls == [call(mock_sf, m_conf)]
        assert mock_prov.mock_calls == [call(m_conf, m_partial)]
        assert mock_config.mock_calls == [call()]

    def test_dryrun(self):
        m_partial = Mock(spec_set=partial)
        m_conf = Mock(spec_set=ManheimConfig)
        with patch(
            '%s.MailerStep.mailer_config' % pbm, new_callable=PropertyMock
        ) as mock_config:
            with patch(
                '%s.mailer_deploy.provision' % pbm, autospec=True
            ) as mock_prov:
                with patch(
                    '%s.functools.partial' % pbm, autospec=True
                ) as mock_partial:
                    with patch(
                        '%s.session_factory' % pbm, autospec=True
                    ):
                        mock_config.return_value = m_conf
                        mock_partial.return_value = m_partial
                        runner.MailerStep('rName', self.m_conf).dryrun()
        assert mock_partial.mock_calls == []
        assert mock_prov.mock_calls == []
        assert mock_config.mock_calls == [call()]

    def test_run_in_region(self):
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_conf).mailer_regions = PropertyMock(
            return_value=['us-east-1']
        )
        for rname in ALL_REGIONS:
            if rname == 'us-east-1':
                assert runner.MailerStep.run_in_region(rname, m_conf) is True
            else:
                assert runner.MailerStep.run_in_region(rname, m_conf) is False

    def test_mailer_archive(self):
        """
        This is a test of ``c7n_mailer.deploy.get_archive()``. We've had a few
        dependency issues in the past that aren't detected until actually
        deploying mailer and generating the archive (zip) for the Lambda, so
        this attempts to detect those issues.
        """
        arch = get_archive({'templates_folders': []})
        assert isinstance(arch, PythonPackageArchive)
        assert arch.size > 0
        assert len(arch.get_filenames()) > 0


class TestDryRunDiffStep(StepTester):

    def test_run(self):
        with patch('%s.DryRunDiffer' % pbm, autospec=True) as mock_drd:
            runner.DryRunDiffStep('rName', self.m_conf).run()
        assert mock_drd.mock_calls == []

    def test_dryrun(self):
        with patch('%s.DryRunDiffer' % pbm, autospec=True) as mock_drd:
            runner.DryRunDiffStep('rName', self.m_conf).dryrun()
        assert mock_drd.mock_calls == [
            call(self.m_conf),
            call().run(diff_against='origin/master')
        ]

    def test_run_in_region(self):
        type(self.m_conf).regions = PropertyMock(
            return_value=ALL_REGIONS
        )
        for rname in ALL_REGIONS:
            if rname == 'us-west-2':
                assert runner.DryRunDiffStep.run_in_region(
                    rname, self.m_conf
                ) is True
            else:
                assert runner.DryRunDiffStep.run_in_region(
                    rname, self.m_conf
                ) is False


class TestS3ArchiverStep(StepTester):

    def test_run(self):
        type(self.m_conf).output_s3_bucket_name = PropertyMock(
            return_value='cloud-custodian-ACCT-REGION'
        )
        with patch('%s.S3Archiver' % pbm, autospec=True) as mock_s3a:
            runner.S3ArchiverStep('rName', self.m_conf).run()
        assert mock_s3a.mock_calls == [
            call(
                'rName',
                'cloud-custodian-ACCT-REGION',
                'custodian_rName.yml'
            ),
            call().run()
        ]

    def test_dryrun(self):
        type(self.m_conf).output_s3_bucket_name = PropertyMock(
            return_value='cloud-custodian-ACCT-REGION'
        )
        with patch('%s.S3Archiver' % pbm, autospec=True) as mock_s3a:
            runner.S3ArchiverStep('rName', self.m_conf).dryrun()
        assert mock_s3a.mock_calls == [
            call(
                'rName',
                'cloud-custodian-ACCT-REGION',
                'custodian_rName.yml',
                dryrun=True
            ),
            call().run()
        ]

    def test_run_in_region(self):
        for rname in ALL_REGIONS:
            assert runner.S3ArchiverStep.run_in_region(rname, None) is True


class TestDocsBuildStep(StepTester):

    def test_run(self):
        with patch(
            '%s.DocsBuildStep._run_sphinx_build' % pbm, autospec=True
        ) as m_rsb:
            cls = runner.DocsBuildStep('rName', self.m_conf)
            cls.run()
        assert m_rsb.mock_calls == [call(cls)]

    def test_dryrun(self):
        with patch(
            '%s.DocsBuildStep._run_sphinx_build' % pbm, autospec=True
        ) as m_rsb:
            cls = runner.DocsBuildStep('rName', self.m_conf)
            cls.dryrun()
        assert m_rsb.mock_calls == [call(cls)]

    def test_run_sphinx_build(self):
        with patch('%s.os.path.exists' % pbm, autospec=True) as mock_ope:
            with patch('%s.rmtree' % pbm, autospec=True) as mock_rmtree:
                with patch(
                    '%s.sphinx_main' % pbm, autospec=True
                ) as mock_sphinx:
                    mock_ope.return_value = False
                    mock_sphinx.return_value = 0
                    runner.DocsBuildStep(
                        'rName', self.m_conf
                    )._run_sphinx_build()
        assert mock_ope.mock_calls == [call('docs/_build')]
        assert mock_rmtree.mock_calls == []
        assert mock_sphinx.mock_calls == [
            call(['-W', 'docs/source', 'docs/_build', '-b', 'dirhtml'])
        ]

    def test_run_sphinx_build_failure(self):
        with patch('%s.os.path.exists' % pbm, autospec=True) as mock_ope:
            with patch('%s.rmtree' % pbm, autospec=True) as mock_rmtree:
                with patch(
                    '%s.sphinx_main' % pbm, autospec=True
                ) as mock_sphinx:
                    mock_ope.return_value = True
                    mock_sphinx.return_value = 3
                    with pytest.raises(RuntimeError) as exc:
                        runner.DocsBuildStep(
                            'rName', self.m_conf
                        )._run_sphinx_build()
        assert str(exc.value) == 'Sphinx exited 3'
        assert mock_ope.mock_calls == [call('docs/_build')]
        assert mock_rmtree.mock_calls == [call('docs/_build')]
        assert mock_sphinx.mock_calls == [
            call(['-W', 'docs/source', 'docs/_build', '-b', 'dirhtml'])
        ]

    def test_run_in_region(self):
        conf = FakeConfig(ALL_REGIONS)
        for rname in ALL_REGIONS:
            if rname == ALL_REGIONS[0]:
                assert runner.DocsBuildStep.run_in_region(rname, conf) is True
            else:
                assert runner.DocsBuildStep.run_in_region(rname, conf) is False


class TestStepClasses(object):

    def test_all_subclasses_have_unique_name(self):
        subc = [x for x in runner.BaseStep.__subclasses__()]
        names = []
        for x in subc:
            assert x.name is not None
            names.append(x.name.strip())
        assert len(names) == len(set(names))
        assert None not in names
        assert '' not in names

    def test_base_step_run_in_region(self):
        assert runner.BaseStep.run_in_region('foo', None) is True


class TestCustodianRunner(object):

    def setup(self):

        def se_cls2(rname, r_conf):
            return rname in ['r1', 'r3']

        def se_cls3(rname, r_conf):
            return rname == 'r1'

        self.cls1 = Mock(spec_set=BaseStep)
        type(self.cls1).name = PropertyMock(return_value='cls1')
        self.cls1.run_in_region.return_value = True
        self.cls2 = Mock(spec_set=BaseStep)
        type(self.cls2).name = PropertyMock(return_value='cls2')
        self.cls2.run_in_region.side_effect = se_cls2
        self.cls3 = Mock(spec_set=BaseStep)
        type(self.cls3).name = PropertyMock(return_value='cls3')
        self.cls3.run_in_region.side_effect = se_cls3
        self.cls4 = Mock(spec_set=BaseStep)
        type(self.cls4).name = PropertyMock(return_value='cls4')
        self.cls4.run_in_region.return_value = True
        self.steps = [self.cls1, self.cls2, self.cls3, self.cls4]

    def test_init(self):
        m_conf = Mock(spec_set=ManheimConfig)
        with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
            mock_cff.return_value = m_conf
            cls = runner.CustodianRunner('acctName', 'cpath')
        assert cls.config == m_conf
        assert cls._config_path == 'cpath'
        assert mock_cff.mock_calls == [call('cpath', 'acctName')]

    def test_run_all_steps(self):
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_conf).regions = PropertyMock(
            return_value=['r1', 'r2', 'r3']
        )
        with patch('%s.CustodianRunner.ordered_step_classes' % pbm, self.steps):
            with patch.multiple(
                '%s.CustodianRunner' % pbm,
                autospec=True,
                _steps_to_run=DEFAULT,
                _run_step_in_regions=DEFAULT,
                _validate_account=DEFAULT
            ) as mocks:
                mocks['_steps_to_run'].return_value = [
                    self.cls1, self.cls2, self.cls3, self.cls4
                ]
                with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                    with patch(
                        '%s.ManheimConfig.from_file' % pbm
                    ) as mock_cff:
                        mock_cff.return_value = m_conf
                        cls = runner.CustodianRunner('acctName')
                        cls.run('run')
        assert mocks['_steps_to_run'].mock_calls == [call(cls, [], [])]
        assert mocks['_run_step_in_regions'].mock_calls == [
            call(cls, 'run', self.cls1, ['r1', 'r2', 'r3']),
            call(cls, 'run', self.cls2, ['r1', 'r2', 'r3']),
            call(cls, 'run', self.cls3, ['r1', 'r2', 'r3']),
            call(cls, 'run', self.cls4, ['r1', 'r2', 'r3'])
        ]
        assert self.cls1.mock_calls == []
        assert self.cls2.mock_calls == []
        assert self.cls3.mock_calls == []
        assert self.cls4.mock_calls == []
        assert mock_logger.mock_calls == [
            call.info(bold('Beginning run - 4 steps')),
            call.info(bold('Step 1 of 4 - cls1')),
            call.info(bold('Step 2 of 4 - cls2')),
            call.info(bold('Step 3 of 4 - cls3')),
            call.info(bold('Step 4 of 4 - cls4')),
            call.info(bold('SUCCESS: All 4 steps complete!'))
        ]
        assert mock_cff.mock_calls == [
            call('manheim-c7n-tools.yml', 'acctName')
        ]
        assert mocks['_validate_account'].mock_calls == [call(cls)]

    def test_run_dryrun_some_steps_some_regions(self):
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_conf).regions = PropertyMock(
            return_value=['r1', 'r2', 'r3']
        )
        with patch('%s.CustodianRunner.ordered_step_classes' % pbm, self.steps):
            with patch.multiple(
                '%s.CustodianRunner' % pbm,
                autospec=True,
                _steps_to_run=DEFAULT,
                _run_step_in_regions=DEFAULT,
                _validate_account=DEFAULT
            ) as mocks:
                mocks['_steps_to_run'].return_value = [
                    self.cls2, self.cls3
                ]
                with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                    with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
                        mock_cff.return_value = m_conf
                        cls = runner.CustodianRunner('aName')
                        cls.run(
                            'dryrun',
                            regions=['r2'],
                            step_names=['cls2', 'cls3', 'cls4'],
                            skip_steps=['cls4']
                        )
        assert mocks['_steps_to_run'].mock_calls == [
            call(cls, ['cls2', 'cls3', 'cls4'], ['cls4'])
        ]
        assert mocks['_run_step_in_regions'].mock_calls == [
            call(cls, 'dryrun', self.cls2, ['r2']),
            call(cls, 'dryrun', self.cls3, ['r2'])
        ]
        assert self.cls1.mock_calls == []
        assert self.cls2.mock_calls == []
        assert self.cls3.mock_calls == []
        assert self.cls4.mock_calls == []
        assert mock_logger.mock_calls == [
            call.info(bold('Beginning dryrun - 2 of 4 steps selected')),
            call.info(bold('Step 1 of 2 - cls2')),
            call.info(bold('Step 2 of 2 - cls3')),
            call.info(bold('SUCCESS: All 2 steps complete!'))
        ]
        assert mock_cff.mock_calls == [call('manheim-c7n-tools.yml', 'aName')]
        assert mocks['_validate_account'].mock_calls == [call(cls)]

    def test_run_invalid_region_name(self):
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_conf).regions = PropertyMock(
            return_value=['r1', 'r2', 'r3']
        )
        with patch('%s.CustodianRunner.ordered_step_classes' % pbm, self.steps):
            with patch.multiple(
                '%s.CustodianRunner' % pbm,
                autospec=True,
                _steps_to_run=DEFAULT,
                _run_step_in_regions=DEFAULT,
                _validate_account=DEFAULT
            ) as mocks:
                mocks['_steps_to_run'].return_value = [
                    self.cls2, self.cls3
                ]
                with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                    with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
                        mock_cff.return_value = m_conf
                        with pytest.raises(RuntimeError) as exc:
                            cls = runner.CustodianRunner('acctName')
                            cls.run(
                                'dryrun',
                                regions=['notValid'],
                                step_names=['cls2', 'cls3', 'cls4'],
                                skip_steps=['cls4']
                            )
        assert str(exc.value) == 'ERROR: All specified region names must be ' \
                                 'listed in the "regions" section of the ' \
                                 'config file (manheim-c7n-tools.yml)'
        assert mocks['_steps_to_run'].mock_calls == [
            call(cls, ['cls2', 'cls3', 'cls4'], ['cls4'])
        ]
        assert mocks['_run_step_in_regions'].mock_calls == []
        assert self.cls1.mock_calls == []
        assert self.cls2.mock_calls == []
        assert self.cls3.mock_calls == []
        assert self.cls4.mock_calls == []
        assert mock_logger.mock_calls == [
            call.info(bold('Beginning dryrun - 2 of 4 steps selected'))
        ]
        assert mocks['_validate_account'].mock_calls == [call(cls)]

    def test_validate_account(self):
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_conf).account_name = PropertyMock(
            return_value='myAcct'
        )
        type(m_conf).account_id = PropertyMock(return_value='0234567890')

        with patch('%s.boto3.client' % pbm) as mock_client:
            mock_client.return_value.get_caller_identity.return_value = {
                'UserId': 'MyUID',
                'Arn': 'myARN',
                'Account': '0234567890'
            }
            with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
                mock_cff.return_value = m_conf
                cls = runner.CustodianRunner('acctName')
                cls._validate_account()
        assert mock_cff.mock_calls == [
            call('manheim-c7n-tools.yml', 'acctName')
        ]
        assert mock_client.mock_calls == [
            call('sts', region_name='us-east-1'),
            call().get_caller_identity()
        ]

    def test_validate_account_failed(self):
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_conf).account_name = PropertyMock(
            return_value='myAcct'
        )
        type(m_conf).account_id = PropertyMock(return_value='1234567890')

        with patch('%s.boto3.client' % pbm) as mock_client:
            mock_client.return_value.get_caller_identity.return_value = {
                'UserId': 'MyUID',
                'Arn': 'myARN',
                'Account': '9876543210'
            }
            with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
                mock_cff.return_value = m_conf
                cls = runner.CustodianRunner('acctName')
                with pytest.raises(RuntimeError) as exc:
                    cls._validate_account()
        assert str(exc.value) == 'ERROR: Using configuration for account ' \
                                 '1234567890 (myAcct), but ' \
                                 'sts:GetCallerIdentity reports connected to ' \
                                 'account 9876543210'
        assert mock_cff.mock_calls == [
            call('manheim-c7n-tools.yml', 'acctName')
        ]
        assert mock_client.mock_calls == [
            call('sts', region_name='us-east-1'),
            call().get_caller_identity()
        ]

    def test_steps_to_run_all(self):
        m_conf = Mock(spec_set=ManheimConfig)
        with patch('%s.CustodianRunner.ordered_step_classes' % pbm, self.steps):
            with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
                mock_cff.return_value = m_conf
                res = runner.CustodianRunner('acctName')._steps_to_run([], [])
        assert res == self.steps

    def test_steps_to_run_step_names(self):
        m_conf = Mock(spec_set=ManheimConfig)
        with patch('%s.CustodianRunner.ordered_step_classes' % pbm, self.steps):
            with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
                mock_cff.return_value = m_conf
                res = runner.CustodianRunner('acctName')._steps_to_run(
                    ['cls3', 'cls1'], []
                )
        assert res == [self.cls1, self.cls3]

    def test_steps_to_run_skip_steps(self):
        m_conf = Mock(spec_set=ManheimConfig)
        with patch('%s.CustodianRunner.ordered_step_classes' % pbm, self.steps):
            with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
                mock_cff.return_value = m_conf
                res = runner.CustodianRunner('aName')._steps_to_run(
                    [], ['cls4', 'cls2']
                )
        assert res == [self.cls1, self.cls3]

    def test_steps_to_run_names_and_skip(self):
        m_conf = Mock(spec_set=ManheimConfig)
        with patch('%s.CustodianRunner.ordered_step_classes' % pbm, self.steps):
            with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
                mock_cff.return_value = m_conf
                res = runner.CustodianRunner('aName')._steps_to_run(
                    ['cls3', 'cls2', 'cls1'], ['cls1']
                )
        assert res == [self.cls2, self.cls3]

    def test_ordered_step_classes(self):
        """ensures all are subclasses of BaseStep"""
        m_conf = Mock(spec_set=ManheimConfig)
        for klass in runner.CustodianRunner.ordered_step_classes:
            with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
                mock_cff.return_value = m_conf
                assert isinstance(klass(None, m_conf), runner.BaseStep)

    def test_run_in_regions_run(self):
        m_conf = Mock(spec_set=ManheimConfig)
        m_conf_r1 = Mock(spec_set=ManheimConfig)
        m_conf_r2 = Mock(spec_set=ManheimConfig)
        m_conf_r3 = Mock(spec_set=ManheimConfig)

        def se_conf_for_region(rname):
            if rname == 'r1':
                return m_conf_r1
            if rname == 'r2':
                return m_conf_r2
            if rname == 'r3':
                return m_conf_r3

        m_conf.config_for_region.side_effect = se_conf_for_region

        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
                mock_cff.return_value = m_conf
                runner.CustodianRunner('acctName')._run_step_in_regions(
                    'run', self.cls1, ['r1', 'r2', 'r3']
                )
        assert self.cls1.mock_calls == [
            call.run_in_region('r1', m_conf_r1),
            call('r1', m_conf_r1),
            call().run(),
            call.run_in_region('r2', m_conf_r2),
            call('r2', m_conf_r2),
            call().run(),
            call.run_in_region('r3', m_conf_r3),
            call('r3', m_conf_r3),
            call().run()
        ]
        assert m_conf.config_for_region.mock_calls == [
            call('r1'),
            call('r2'),
            call('r3')
        ]
        assert mock_logger.mock_calls == [
            call.info(bold('Step cls1 in REGION 1 of 3 (r1)')),
            call.info(bold('Step cls1 in REGION 2 of 3 (r2)')),
            call.info(bold('Step cls1 in REGION 3 of 3 (r3)'))
        ]

    def test_run_in_regions_policygen_run(self):
        m_conf = Mock(spec_set=ManheimConfig)
        m_conf_r1 = Mock(spec_set=ManheimConfig)
        m_conf_r2 = Mock(spec_set=ManheimConfig)
        m_conf_r3 = Mock(spec_set=ManheimConfig)

        def se_conf_for_region(rname):
            if rname == 'r1':
                return m_conf_r1
            if rname == 'r2':
                return m_conf_r2
            if rname == 'r3':
                return m_conf_r3

        m_conf.config_for_region.side_effect = se_conf_for_region

        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
                mock_cff.return_value = m_conf
                with patch('%s.PolicygenStep' % pbm, autospec=True) as mock_pgs:
                    type(mock_pgs).name = PropertyMock(return_value='policygen')
                    mock_pgs.run_in_region.return_value = True
                    runner.CustodianRunner('acctName')._run_step_in_regions(
                        'run', mock_pgs, ['r1', 'r2', 'r3']
                    )
        assert mock_pgs.mock_calls == [
            call.run_in_region('r1', m_conf),
            call('r1', m_conf),
            call().run(),
            call.run_in_region('r2', m_conf),
            call('r2', m_conf),
            call().run(),
            call.run_in_region('r3', m_conf),
            call('r3', m_conf),
            call().run()
        ]
        assert m_conf.config_for_region.mock_calls == []
        assert mock_logger.mock_calls == [
            call.info(bold('Step policygen in REGION 1 of 3 (r1)')),
            call.info(bold('Step policygen in REGION 2 of 3 (r2)')),
            call.info(bold('Step policygen in REGION 3 of 3 (r3)'))
        ]

    def test_run_in_regions_dryrun_skip_some(self):
        m_conf = Mock(spec_set=ManheimConfig)
        m_conf_r1 = Mock(spec_set=ManheimConfig)
        m_conf_r2 = Mock(spec_set=ManheimConfig)
        m_conf_r3 = Mock(spec_set=ManheimConfig)

        def se_conf_for_region(rname):
            if rname == 'r1':
                return m_conf_r1
            if rname == 'r2':
                return m_conf_r2
            if rname == 'r3':
                return m_conf_r3

        m_conf.config_for_region.side_effect = se_conf_for_region

        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.ManheimConfig.from_file' % pbm) as mock_cff:
                mock_cff.return_value = m_conf
                runner.CustodianRunner('acctName')._run_step_in_regions(
                    'dryrun', self.cls2, ['r2', 'r3']
                )
        assert self.cls2.mock_calls == [
            call.run_in_region('r2', m_conf_r2),
            call.run_in_region('r3', m_conf_r3),
            call('r3', m_conf_r3),
            call().dryrun()
        ]
        assert m_conf.config_for_region.mock_calls == [
            call('r2'),
            call('r3')
        ]
        assert mock_logger.mock_calls == [
            call.info(bold('SKIPPING Step cls2 in REGION 1 of 2 (r2)')),
            call.info(bold('Step cls2 in REGION 2 of 2 (r3)'))
        ]


class TestParseArgs(object):

    def test_run(self):
        p = runner.parse_args(['run', 'aName'])
        assert p.verbose == 0
        assert p.steps == []
        assert p.skip == []
        assert p.ACTION == 'run'
        assert p.regions == []
        assert p.config == 'manheim-c7n-tools.yml'
        assert p.ACCT_NAME == 'aName'
        assert p.assume_role is True

    def test_run_skip_steps(self):
        p = runner.parse_args(
            ['-S', 'foo', '--skip-step=bar', 'run', 'acctName']
        )
        assert p.verbose == 0
        assert p.steps == []
        assert p.skip == ['foo', 'bar']
        assert p.ACTION == 'run'
        assert p.regions == []
        assert p.config == 'manheim-c7n-tools.yml'
        assert p.ACCT_NAME == 'acctName'
        assert p.assume_role is True

    def test_dryrun_info_region(self):
        p = runner.parse_args(['-v', '-r', 'us-east-1', 'dryrun', 'aName'])
        assert p.verbose == 1
        assert p.steps == []
        assert p.skip == []
        assert p.ACTION == 'dryrun'
        assert p.regions == ['us-east-1']
        assert p.config == 'manheim-c7n-tools.yml'
        assert p.ACCT_NAME == 'aName'
        assert p.assume_role is True

    def test_list(self):
        p = runner.parse_args(['-c', 'foobar.yml', '--no-assume-role', 'list'])
        assert p.verbose == 0
        assert p.steps == []
        assert p.skip == []
        assert p.ACTION == 'list'
        assert p.regions == []
        assert p.config == 'foobar.yml'
        assert p.assume_role is False

    def test_list_accounts(self):
        p = runner.parse_args(['accounts'])
        assert p.verbose == 0
        assert p.steps == []
        assert p.skip == []
        assert p.ACTION == 'accounts'
        assert p.regions == []
        assert p.config == 'manheim-c7n-tools.yml'
        assert p.assume_role is True

    def test_run_debug_steps_assume_role(self):
        p = runner.parse_args(
            ['-vv', '-A', '-s', 'foo', '--step=bar', 'run', 'aName']
        )
        assert p.verbose == 2
        assert p.steps == ['foo', 'bar']
        assert p.skip == []
        assert p.ACTION == 'run'
        assert p.regions == []
        assert p.config == 'manheim-c7n-tools.yml'
        assert p.ACCT_NAME == 'aName'
        assert p.assume_role is False


class FakeArgs(object):
    verbose = 0
    list = False
    steps = []
    skip = []
    ACTION = None
    regions = []
    config = 'manheim-c7n-tools.yml'
    ACCT_NAME = 'acctName'
    assume_role = True

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestMain(object):

    def test_run(self, capsys):
        m_cr = Mock(spec_set=runner.CustodianRunner)
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_cr).config = m_conf
        with patch.multiple(
            pbm,
            autospec=True,
            parse_args=DEFAULT,
            set_log_debug=DEFAULT,
            set_log_info=DEFAULT,
            CustodianRunner=DEFAULT,
            ManheimConfig=DEFAULT,
            assume_role=DEFAULT
        ) as mocks:
            mocks['parse_args'].return_value = FakeArgs(
                ACTION='run', regions=['foo2'], assume_role=False
            )
            mocks['CustodianRunner'].return_value = m_cr
            runner.main()
        captured = capsys.readouterr()
        assert mocks['parse_args'].mock_calls == [
            call(sys.argv[1:])
        ]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['CustodianRunner'].mock_calls == [
            call('acctName', 'manheim-c7n-tools.yml'),
            call().run(
                'run', ['foo2'], step_names=[], skip_steps=[]
            )
        ]
        assert mocks['ManheimConfig'].mock_calls == []
        assert captured.out == ''
        assert captured.err == ''
        assert mocks['assume_role'].mock_calls == []

    def test_info_list(self, capsys):
        osc = runner.CustodianRunner.ordered_step_classes
        m_cr = Mock(spec_set=runner.CustodianRunner)
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_cr).config = m_conf
        with patch.multiple(
            pbm,
            autospec=True,
            parse_args=DEFAULT,
            set_log_debug=DEFAULT,
            set_log_info=DEFAULT,
            CustodianRunner=DEFAULT,
            ManheimConfig=DEFAULT,
            assume_role=DEFAULT
        ) as mocks:
            mocks['parse_args'].return_value = FakeArgs(
                ACTION='list', verbose=1
            )
            mocks['CustodianRunner'].return_value = m_cr
            type(mocks['CustodianRunner']).ordered_step_classes = osc
            with pytest.raises(SystemExit) as exc:
                runner.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert mocks['parse_args'].mock_calls == [
            call(sys.argv[1:])
        ]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['set_log_info'].mock_calls == [call(runner.logger)]
        assert mocks['ManheimConfig'].mock_calls == []
        expected = "\n".join(
            x.name for x in osc
        )
        assert captured.out == expected + "\n"
        assert captured.err == ''
        assert mocks['assume_role'].mock_calls == []

    def test_accounts(self, capsys):
        m_conf = Mock(spec_set=ManheimConfig)
        osc = runner.CustodianRunner.ordered_step_classes
        m_cr = Mock(spec_set=runner.CustodianRunner)
        type(m_cr).config = m_conf
        with patch.multiple(
            pbm,
            autospec=True,
            parse_args=DEFAULT,
            set_log_debug=DEFAULT,
            set_log_info=DEFAULT,
            CustodianRunner=DEFAULT,
            ManheimConfig=DEFAULT,
            assume_role=DEFAULT
        ) as mocks:
            mocks['parse_args'].return_value = FakeArgs(ACTION='accounts')
            mocks['CustodianRunner'].return_value = m_cr
            type(mocks['CustodianRunner']).ordered_step_classes = osc
            type(mocks['ManheimConfig']).return_value = m_conf
            with patch('%s.ManheimConfig.list_accounts' % pbm) as mock_la:
                mock_la.return_value = {
                    'acct1': 1111,
                    'acct3': 3333,
                    'acct2': 2222
                }
                with pytest.raises(SystemExit) as exc:
                    runner.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert mocks['parse_args'].mock_calls == [
            call(sys.argv[1:])
        ]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['ManheimConfig'].mock_calls == []
        assert mock_la.mock_calls == [call('manheim-c7n-tools.yml')]
        assert captured.out == "acct1 (1111)\nacct2 (2222)\nacct3 (3333)\n"
        assert captured.err == ''
        assert mocks['assume_role'].mock_calls == []

    def test_debug_dryrun_assume_role(self, capsys):
        m_cr = Mock(spec_set=runner.CustodianRunner)
        m_conf = Mock(spec_set=ManheimConfig)
        type(m_cr).config = m_conf
        with patch.multiple(
            pbm,
            autospec=True,
            parse_args=DEFAULT,
            set_log_debug=DEFAULT,
            set_log_info=DEFAULT,
            CustodianRunner=DEFAULT,
            ManheimConfig=DEFAULT,
            assume_role=DEFAULT
        ) as mocks:
            mocks['parse_args'].return_value = FakeArgs(
                ACTION='dryrun', verbose=2, steps=['foo'], skip=['bar'],
                config='foo.yml', ACCT_NAME='aName', assume_role=True
            )
            mocks['CustodianRunner'].return_value = m_cr
            runner.main()
        captured = capsys.readouterr()
        assert mocks['parse_args'].mock_calls == [
            call(sys.argv[1:])
        ]
        assert mocks['set_log_debug'].mock_calls == [call(runner.logger)]
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['CustodianRunner'].mock_calls == [
            call('aName', 'foo.yml'),
            call().run(
                'dryrun', [], step_names=['foo'], skip_steps=['bar']
            )
        ]
        assert mocks['ManheimConfig'].mock_calls == []
        assert captured.out == ''
        assert captured.err == ''
        assert mocks['assume_role'].mock_calls == [call(m_conf)]
