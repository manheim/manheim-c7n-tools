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
Command-line entrypoint to run one/multiple/all steps of a c7n deployment.

The command-line entrypoint function (:py:func:`~.main`) instantiates an
instance of :py:class:`~.CustodianRunner` and calls its
:py:meth:`~.CustodianRunner.run` method. This iterates through all of the
classes listed in :py:attr:`~.CustodianRunner.ordered_step_classes` and calls
their ``run`` or ``dryrun`` methods depending on which was specified on the
command line.
"""

import sys
import logging
import argparse
import abc
import functools
from shutil import rmtree
import os
from copy import deepcopy

from sphinx.cmd.build import main as sphinx_main
import jsonschema
import boto3

from c7n.commands import validate, run
from c7n.config import Config
from c7n.policy import PolicyCollection
from c7n_mailer.cli import session_factory
from c7n_mailer.cli import CONFIG_SCHEMA as MAILER_SCHEMA
from c7n_mailer.utils import setup_defaults as mailer_setup_defaults
from c7n_mailer import deploy as mailer_deploy

from manheim_c7n_tools.utils import (
    set_log_info, set_log_debug, bold, assume_role
)
from manheim_c7n_tools.version import VERSION, PROJECT_URL
from manheim_c7n_tools.policygen import PolicyGen
from manheim_c7n_tools.vendor.mugc import (
    load_policies, resources_gc_prefix, AWS
)
from manheim_c7n_tools.dryrun_diff import DryRunDiffer
from manheim_c7n_tools.s3_archiver import S3Archiver
from manheim_c7n_tools.config import ManheimConfig

FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger()

for lname in ['boto3', 'botocore', 'urllib', 'urllib3']:
    # suppress library logging below WARNING level
    log = logging.getLogger(lname)
    log.setLevel(logging.WARNING)
    log.propagate = True


class BaseStep(object):
    """
    Base class representing one step in the deployment process. Subclass this
    for each step. It should have a name and two public methods, ``run`` and
    ``dryrun``.
    """

    __metaclass__ = abc.ABCMeta

    #: The name of the step, as used on the CLI
    name = None

    def __init__(self, region_name, config):
        """
        Base Step class initializer.

        Steps should ONLY ever be initialized by
        :py:meth:`~.CustodianRunner._run_step_in_regions`.

        :param region_name: region name to run this step against
        :type region_name: str
        :param config: The manheim-c7n-tools config to use for this step,
          already made region-specific
          (:py:meth:`~.ManheimConfig.config_for_region` is called where this
          class is intialized in
          :py:meth:`~.CustodianRunner._run_step_in_regions`).
        :type config: ManheimConfig
        """
        self.region_name = region_name
        self.config = config

    @abc.abstractmethod
    def run(self):
        pass  # nocoverage

    @abc.abstractmethod
    def dryrun(self):
        pass  # nocoverage

    @staticmethod
    def run_in_region(region_name, config):
        """
        Return True if this step should run in the specified region,
        False if it should not.

        :param region_name: region name to test
        :type region_name: str
        :param config: The manheim-c7n-tools config to use for this step,
          already made region-specific
          (:py:meth:`~.ManheimConfig.config_for_region` is called where this
          class is intialized in
          :py:meth:`~.CustodianRunner._run_step_in_regions`).
        :type config: ManheimConfig
        :return: whether this step should run in the specified region
        :rtype: bool
        """
        return True


class PolicygenStep(BaseStep):
    """Step to run policygen to generate custodian-ready policies on disk."""

    name = 'policygen'

    def _do_policygen(self):
        PolicyGen(self.config).run()

    def run(self):
        self._do_policygen()

    def dryrun(self):
        self._do_policygen()

    @staticmethod
    def run_in_region(region_name, conf):
        # only run in the first-configured region
        return region_name == conf.regions[0]


class ValidateStep(BaseStep):
    """Step to run custodian validate on generated policies."""

    name = 'validate'

    def _do_validate(self):
        conf = Config.empty(
            configs=['custodian_%s.yml' % self.region_name],
            region=self.region_name
        )
        validate(conf)

    def run(self):
        self._do_validate()

    def dryrun(self):
        self._do_validate()


class MugcStep(BaseStep):
    """
    Step to run custodian mugc.py (lambda garbage collection), based on main()
    in that module.
    """

    name = 'mugc'

    def run(self):
        # This is largely based off of mugc.main()
        logging.getLogger('botocore').setLevel(logging.ERROR)
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        logging.getLogger('c7n.cache').setLevel(logging.WARNING)
        conf = Config.empty(
            config_files=['custodian_%s.yml' % self.region_name],
            regions=[self.region_name],
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
        # use cloud provider to initialize policies to get region expansion
        policies = AWS().initialize_policies(
            PolicyCollection(
                [
                    p for p in load_policies(conf, conf)
                    if p.provider_name == 'aws'
                ],
                conf
            ),
            conf
        )
        resources_gc_prefix(conf, conf, policies)

    def dryrun(self):
        # This is largely based off of mugc.main()
        logging.getLogger('botocore').setLevel(logging.ERROR)
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        logging.getLogger('c7n.cache').setLevel(logging.WARNING)
        conf = Config.empty(
            config_files=['custodian_%s.yml' % self.region_name],
            regions=[self.region_name],
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
        # use cloud provider to initialize policies to get region expansion
        policies = AWS().initialize_policies(
            PolicyCollection(
                [
                    p for p in load_policies(conf, conf)
                    if p.provider_name == 'aws'
                ],
                conf
            ),
            conf
        )
        resources_gc_prefix(conf, conf, policies)


class CustodianStep(BaseStep):
    """Step for actual custodian run"""

    name = 'custodian'

    def run(self):
        """
        Perform an actual run of cloud-custodian.

        This replicates the command:
        custodian run --region '${region}' --metrics -v -s \
          cloud-custodian-${account_id}-${region}/logs \
          --log-group=/cloud-custodian/${account_id}/${region} \
          -c custodian_${region}.yml \
          --cache '/tmp/.cache/cloud-custodian.cache'
        """
        conf = Config.empty(
            configs=['custodian_%s.yml' % self.region_name],
            region=self.region_name,
            regions=[self.region_name],
            log_group=self.config.custodian_log_group,
            verbose=1,
            metrics_enabled=True,
            subparser='run',
            cache='/tmp/.cache/cloud-custodian.cache',
            command='c7n.commands.run',
            output_dir='%s/logs' % self.config.output_s3_bucket_name,
            vars=None,
            dryrun=False
        )
        run(conf)

    def dryrun(self):
        """
        Perform a dry-run of custodian.

        This replicates the command:

        custodian run --region '${region}' --dryrun -v -s dryrun/${region} \
          -c custodian_${region}.yml \
          --cache '/tmp/.cache/cloud-custodian.cache'
        """
        conf = Config.empty(
            configs=['custodian_%s.yml' % self.region_name],
            region=self.region_name,
            regions=[self.region_name],
            verbose=1,
            metrics_enabled=False,
            subparser='run',
            cache='/tmp/.cache/cloud-custodian.cache',
            command='c7n.commands.run',
            output_dir='dryrun/%s' % self.region_name,
            vars=None,
            dryrun=True
        )
        run(conf)


class MailerStep(BaseStep):
    """
    Step for running c7n-mailer dryrun or Lambda provision

    This replicates the parts of c7n_mailer.cli that we need for our use case.
    """

    name = 'mailer'

    @property
    def mailer_config(self):
        """
        Return the validated c7n-mailer config.

        :return: c7n-mailer config
        """
        conf = deepcopy(self.config.mailer_config)
        jsonschema.validate(conf, MAILER_SCHEMA)
        mailer_setup_defaults(conf)
        logger.debug('Default mailer config: %s', conf)
        if 'templates_folders' not in conf:
            conf['templates_folders'] = []
        for d in [
            os.path.abspath('./mailer-templates'),
            '/manheim_c7n_tools/manheim_c7n_tools/mailer-templates',
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'mailer-templates'
            )
        ]:
            if os.path.isdir(d):
                conf['templates_folders'].insert(0, d)
        logger.info('Generated mailer config: %s', conf)
        return conf

    def run(self):
        conf = self.mailer_config
        mailer_deploy.provision(
            conf,
            functools.partial(session_factory, conf)
        )

    def dryrun(self):
        # The only dryrun that mailer has right now is config validation
        self.mailer_config

    @staticmethod
    def run_in_region(region_name, config):
        return region_name in config.mailer_regions


class DryRunDiffStep(BaseStep):
    """Generates the dryrun diff during dry runs."""

    name = 'dryrun-diff'

    def run(self):
        logger.info('Nothing to do during normal run.')

    def dryrun(self):
        DryRunDiffer(self.config).run(diff_against='origin/master')

    @staticmethod
    def run_in_region(region_name, conf):
        return region_name == conf.regions[-1]


class S3ArchiverStep(BaseStep):
    """Runs s3archiver to archive logs of deleted policies."""

    name = 's3archiver'

    def run(self):
        S3Archiver(
            self.region_name,
            self.config.output_s3_bucket_name,
            'custodian_%s.yml' % self.region_name
        ).run()

    def dryrun(self):
        S3Archiver(
            self.region_name,
            self.config.output_s3_bucket_name,
            'custodian_%s.yml' % self.region_name,
            dryrun=True
        ).run()


class DocsBuildStep(BaseStep):
    """Builds generated documentation."""

    name = 'docs'

    def _run_sphinx_build(self):
        if os.path.exists('docs/_build'):
            logger.info('Removing docs/_build')
            rmtree('docs/_build')
        # "sphinx-build -W docs/source docs/_build -b dirhtml"
        argv = ['-W', 'docs/source', 'docs/_build', '-b', 'dirhtml']
        logger.info('Running: sphinx-build %s' % ' '.join(argv))
        rcode = sphinx_main(argv)
        if rcode != 0:
            raise RuntimeError('Sphinx exited %d' % rcode)

    def run(self):
        self._run_sphinx_build()

    def dryrun(self):
        self._run_sphinx_build()

    @staticmethod
    def run_in_region(region_name, conf):
        # only run in the first-configured region
        return region_name == conf.regions[0]


class CustodianRunner(object):
    """
    Main class to run all steps required for manheim c7n deployment.
    """

    #: List of the :py:class:`~.BaseStep` subclasses to run for deployment,
    #: in the order they should be run.
    ordered_step_classes = [
        PolicygenStep,
        ValidateStep,
        MugcStep,
        CustodianStep,
        MailerStep,
        DryRunDiffStep,
        S3ArchiverStep,
        DocsBuildStep
    ]

    def __init__(self, account_name, config_path='manheim-c7n-tools.yml'):
        """
        Initialize the Runner.

        :param account_name: name of the account to run against
        :type account_name: str
        :param config_path: path to ``manheim-c7n-tools.yml`` config file
        :type config_path: str
        """
        self._config_path = config_path
        self.config = ManheimConfig.from_file(config_path, account_name)

    def _steps_to_run(self, step_names, skip_steps):
        """
        Given the ``step_names`` and ``skip_steps`` passed to :py:meth:`~.run`,
        return the list of step classes to run (in order).

        :param step_names: list of step names to run
        :type step_names: list
        :param skip_steps: list of step names to skip
        :type skip_steps: list
        :return: list of step classes to run, in order
        :rtype: list
        """
        if not step_names and not skip_steps:
            # both lists are empty, run everything
            return self.ordered_step_classes
        if not step_names:
            # we only had skip_steps, so start with the list of all steps
            step_names = [x.name for x in self.ordered_step_classes]
        return [
            x for x in self.ordered_step_classes
            if x.name in step_names and x.name not in skip_steps
        ]

    def run(self, action, regions=[], step_names=[], skip_steps=[]):
        """
        Main method to run all steps. This calls :py:meth:`~._steps_to_run`
        to determine which step classes to run and the order to run them in,
        and then loops through that list calling the :py:meth:`~.BaseStep.run`
        or :py:meth:`~.BaseStep.dryrun` method on each of them, according to the
        ``action`` specified.

        :param action: Name of the action to do, "run" or "dryrun"
        :type action: str
        :param regions: list of string region names to run in; if left empty,
          run in all regions listed in config file
        :type regions: list
        :param step_names: list of string step names to run; if not specified,
          will run all defined steps. Steps are always run in the order defined
          in :py:attr:`~.ordered_step_classes`.
        :type step_names: list
        :param skip_steps: list of string step names to skip running
        :type skip_steps: list
        """
        self._validate_account()
        to_run = self._steps_to_run(step_names, skip_steps)
        if to_run == self.ordered_step_classes:
            logger.info(bold(
                'Beginning %s - %d steps' % (action, len(to_run))
            ))
        else:
            logger.info(bold(
                'Beginning %s - %d of %d steps selected' % (
                    action, len(to_run), len(self.ordered_step_classes)
                )
            ))
        if regions:
            if not set(regions).issubset(set(self.config.regions)):
                raise RuntimeError(
                    'ERROR: All specified region names must be listed in the '
                    '"regions" section of the config file '
                    '(%s)' % self._config_path
                )
        else:
            # use all regions from config file
            regions = self.config.regions
        for idx, step in enumerate(to_run):
            logger.info(bold(
                'Step %d of %d - %s' % (idx + 1, len(to_run), step.name)
            ))
            self._run_step_in_regions(action, step, regions)
        logger.info(bold('SUCCESS: All %d steps complete!' % len(to_run)))

    def _validate_account(self):
        """
        Validate that we are connected to the configured account.

        :raises: RuntimeError
        """
        logger.debug('Connecting to STS in us-east-1 to verify account')
        sts = boto3.client('sts', region_name='us-east-1')
        cid = sts.get_caller_identity()
        logger.debug('Caller Identity: %s', cid)
        if cid['Account'] != self.config.account_id:
            raise RuntimeError(
                'ERROR: Using configuration for account %s (%s), but '
                'sts:GetCallerIdentity reports connected to account %s' % (
                    self.config.account_id, self.config.account_name,
                    cid['Account']
                )
            )

    def _run_step_in_regions(self, action, step, regions):
        """
        Called from :py:meth:`~.run`; run a given step in all applicable /
        specified regions.

        :param action: Name of the action to do, "run" or "dryrun"
        :type action: str
        :param step: A reference to the :py:class:`~.BaseStep` subclass to run
        :type step: object
        :param regions: list of string region names to run in
        :type regions: list
        """
        for r_idx, region_name in enumerate(regions):
            if step.name in ['policygen', 'dryrun-diff']:
                # Some steps need a config with %%AWS_REGION%% un-interpolated
                region_conf = self.config
            else:
                region_conf = self.config.config_for_region(region_name)
            if not step.run_in_region(region_name, region_conf):
                logger.info(bold(
                    'SKIPPING Step %s in REGION %d of %d (%s)' % (
                        step.name, r_idx + 1, len(regions), region_name
                    )
                ))
                continue
            logger.info(bold(
                'Step %s in REGION %d of %d (%s)' % (
                    step.name, r_idx + 1, len(regions), region_name
                )
            ))
            if action == 'run':
                step(region_name, region_conf).run()
            else:
                step(region_name, region_conf).dryrun()
            sys.stdout.flush()
            sys.stderr.flush()


def parse_args(argv):
    """Parse command-line arguments with ArgumentParser."""
    p = argparse.ArgumentParser(
        description='manheim-c7n-tools runner; runs one, multiple, or all '
                    'actions for c7n build/deploy',
        epilog='This tool is part of manheim_c7n_tools v%s.\n'
               'For documentation, see: %s' % (VERSION, PROJECT_URL),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-V', '--version', action='version', version=VERSION)
    p.add_argument('-r', '--region', dest='regions', action='append',
                   default=[],
                   help='Region names to run against; may be specified multiple'
                        'times.')
    p.add_argument('-c', '--config', dest='config', action='store',
                   default='manheim-c7n-tools.yml',
                   help='Config file path (default: ./manheim-c7n-tools.yml)')
    p.add_argument('-s', '--step', dest='steps', action='append', default=[],
                   help='Specify one or more steps to run. If not given, will '
                        'run all steps.')
    p.add_argument('-S', '--skip-step', dest='skip', action='append',
                   default=[], help='Specify one or more step names to skip.')
    p.add_argument('-A', '--no-assume-role', dest='assume_role',
                   action='store_false', default=True,
                   help='Do not assume a role, even if  specified in the '
                        'configuration file.')
    subp = p.add_subparsers(help='command', title='subcommands')

    run_parser = subp.add_parser(
        'run', help='Perform a full run (must specify ACCT_NAME)'
    )
    run_parser.set_defaults(ACTION='run')
    dryrun_parser = subp.add_parser(
        'dryrun', help='Perform a dry run (must specify ACCT_NAME)'
    )
    dryrun_parser.set_defaults(ACTION='dryrun')
    list_parser = subp.add_parser('list', help='List available steps')
    list_parser.set_defaults(ACTION='list')
    acct_parser = subp.add_parser('accounts', help='List configured accounts')
    acct_parser.set_defaults(ACTION='accounts')

    for parser in [run_parser, dryrun_parser]:
        parser.add_argument(
            'ACCT_NAME', action='store', type=str, default=None,
            help='account_name value from config file, for account to run '
                 'against'
        )

    args = p.parse_args(argv)
    return args


def main():
    """main command-line entrypoint; calls parse_args, sets up logging, and
    either lists steps or instantiates a CustodianRunner and calls run()."""
    args = parse_args(sys.argv[1:])

    # set logging level
    if args.verbose > 1:
        set_log_debug(logger)
    elif args.verbose == 1:
        set_log_info(logger)

    if args.ACTION == 'list':
        for x in CustodianRunner.ordered_step_classes:
            print(x.name)
        raise SystemExit(0)
    if args.ACTION == 'accounts':
        accts = ManheimConfig.list_accounts(args.config)
        for acctname in sorted(accts.keys()):
            print("%s (%s)" % (acctname, accts[acctname]))
        raise SystemExit(0)
    cr = CustodianRunner(args.ACCT_NAME, args.config)
    if args.assume_role:
        assume_role(cr.config)
    cr.run(
        args.ACTION, args.regions, step_names=args.steps, skip_steps=args.skip
    )


if __name__ == "__main__":
    main()
