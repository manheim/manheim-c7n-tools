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

import jsonschema
import logging
import yaml
import os

from c7n_mailer.cli import CONFIG_SCHEMA as MAILER_SCHEMA

#: Schema of the ``manheim-c7n-tools.yml`` configuration file. This is a schema
#: designed for use with the ``jsonschema`` package. This schema is for ONE
#: ACCOUNT in the config file; the file itself is made up of an array of objects
#: matching this schema.
MANHEIM_CONFIG_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'required': [
        'account_id',
        'account_name',
        'regions',
        'mailer_config',
        'mailer_regions',
        'output_s3_bucket_name',
        'custodian_log_group',
        'dead_letter_queue_arn',
        'role_arn'
    ],
    'properties': {
        # The AWS Account ID
        'account_id': {'type': ['number', 'string']},
        # The AWS account name (should be the official Account Alias)
        'account_name': {'type': 'string'},
        # Optional configuration for a role to assume when running this
        # tooling, for running cross-account.
        'assume_role': {
            'type': 'object',
            'required': ['role_arn'],
            'properties': {
                'role_arn': {'type': 'string'},
                'external_id': {'type': 'string'},
                'duration_seconds': {'type': 'number'}
            }
        },
        # Optional policy source paths. If not specified, uses the current
        # directory
        'policy_source_paths': {'type': 'array', 'items': {'type': 'string'}},
        # A list of region names that custodian should run in for this account
        'regions': {'type': 'array', 'items': {'type': 'string'}},
        # Name of the S3 bucket for storing Custodian output; should include
        # %%AWS_REGION%%, for buckets in each region
        'output_s3_bucket_name': {'type': 'string'},
        # Name of the CloudWatch Log Group to write logs to
        'custodian_log_group': {'type': 'string'},
        # List of region names to run c7n-mailer in
        'mailer_regions': {'type': 'array', 'items': {'type': 'string'}},
        # ARN of the Dead Letter SQS queue
        'dead_letter_queue_arn': {'type': 'string'},
        # ARN of the role to run Lambda functions under
        'role_arn': {'type': 'string'},
        # Array of notification recipients for orphaned Lambda/CWE Rule
        # notifications; set to empty array to disable this functionality
        'cleanup_notify': {'type': 'array'},

        # Optional list of notification targets to add to EVERY policy
        'always_notify': {
            'to': {'type': 'array', 'items': {'type': 'string'}},
            'transport': {
                'oneOf': [
                    {
                        'type': 'object',
                        'required': ['type', 'queue'],
                        'properties': {
                            'queue': {'type': 'string'},
                            'type': {'enum': ['sqs']}
                        }
                    },
                    {
                        'type': 'object',
                        'required': ['type', 'topic'],
                        'properties': {
                            'topic': {'type': 'string'},
                            'type': {'enum': ['sns']},
                            'attributes': {'type': 'object'},
                        }
                    }]
            },
        },

        # Incorporate c7n-mailer's config schema nested under a
        # ``mailer_config`` key. See upstream source of c7n_mailer.
        'mailer_config': MAILER_SCHEMA
    }
}

logger = logging.getLogger(__name__)


class ManheimConfig(object):
    """
    Configuration object for manheim-c7n-tools / :py:mod:`~.runner`.
    """

    def __init__(self, **kwargs):
        self.config_path = kwargs.pop('config_path')
        logger.debug('Validating configuration...')
        jsonschema.validate(kwargs, MANHEIM_CONFIG_SCHEMA)
        self._config = kwargs
        self._config['account_id'] = str(self._config['account_id'])
        if 'cleanup_notify' not in self._config:
            self._config['cleanup_notify'] = []

    @staticmethod
    def from_file(path, account_name):
        """
        Construct a new ManheimConfig object from the YML configuration file
        at the specified path.

        :param path: path of the yaml config file to load
        :type path: str
        :param account_name: top-level account name/alias to load
        :type account_name: str
        :return: new ManheimConfig object for the specified config file
        :rtype: ManheimConfig
        """
        logger.info('Loading config from: %s', path)
        with open(path, 'r') as fh:
            config_dict = yaml.load(fh.read(), Loader=yaml.SafeLoader)
        for acct_conf in config_dict:
            if acct_conf['account_name'] == account_name:
                acct_conf['config_path'] = path
                return ManheimConfig(**acct_conf)
        raise RuntimeError(
            'ERROR: No account with name "%s" in %s' % (
                account_name, path
            )
        )

    @staticmethod
    def list_accounts(path):
        """
        Given the path to a manheim-c7n-tools YML configuration file, return a
        dict of account name to account ID number for each account defined in
        the file.

        :param path: path of the yaml config file to load
        :type path: str
        :return: dict of account name/alias used in the file to Account ID
        :rtype: dict
        """
        logger.info('Loading config from: %s', path)
        with open(path, 'r') as fh:
            config_list = yaml.load(fh.read(), Loader=yaml.SafeLoader)
        return {x['account_name']: str(x['account_id']) for x in config_list}

    def config_for_region(self, region_name):
        """
        Return a copy of this configuration for the specified region name.
        This currently uses an inefficient but simple approach - it serializes
        the current config to a YAML string, replaces all occurrences of
        ``%%AWS_REGION%%`` with the specified ``region_name`` and all
        occurrences of ``%%POLICYGEN_ENV_name%%`` replaced with the value of the
        corresponding environment variable, then deserializes the result and
        returns a new :py:class:`~.ManheimConfig` object using it.

        :param region_name: the region name to build a config for
        :type region_name: str
        :return: new ManheimConfig for the specified region
        :rtype: ManheimConfig
        """
        d = {'config_path': self.config_path}
        d.update(self._config)
        # AWS_REGION replacement
        config_str = yaml.dump(
            d, Dumper=yaml.Dumper
        ).replace('%%AWS_REGION%%', region_name)
        # env var replacements
        for k, v in os.environ.items():
            if not k.startswith('POLICYGEN_ENV_'):
                continue
            config_str = config_str.replace('%%' + k + '%%', v)
        return ManheimConfig(**yaml.load(config_str, Loader=yaml.SafeLoader))

    def __getattr__(self, k):
        try:
            return self._config[k]
        except KeyError:
            raise AttributeError(k)
