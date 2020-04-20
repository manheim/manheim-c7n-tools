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
import os
import re
from copy import deepcopy
from collections import defaultdict
from datetime import datetime
from tabulate import tabulate
import argparse
import logging
import shutil

import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

from manheim_c7n_tools.version import VERSION, PROJECT_URL
from manheim_c7n_tools.config import ManheimConfig
from manheim_c7n_tools.utils import git_html_url

whtspc_re = re.compile(r'\s+')

logger = logging.getLogger(__name__)


def strip_doc(func):
    """
    Given a function or method reference, return its docstring as one line (with
    all newlines removed and all whitespace collapsed).
    """
    d = func.__doc__.replace("\n", " ").strip()
    return whtspc_re.sub(' ', d)


def timestr():
    """just here to make unit testing simpler"""
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC'


class PolicyGen(object):

    def __init__(self, config):
        """
        Initialize the policy generator tool.

        :param config: manheim-c7n-tools configuration object
        :type config: ManheimConfig
        """
        self._config = config
        logger.info(
            'Initialized PolicyGen for account: %s (%s)',
            self._config.account_name, self._config.account_id
        )
        self._policy_sources = defaultdict(set)

    def run(self):
        defaults = self._load_defaults()
        if defaults is None:
            logger.error('Failed to find a `defaults.yml` file')
            raise SystemExit(1)
        acct_configs = self._load_all_policies()
        # generate the per-region configs for each region, for current account
        for rname in self._config.regions:
            self._generate_configs(
                acct_configs[self._config.account_name][rname],
                defaults,
                rname
            )
        logger.info('Writing policy descriptions to policies.rst...')
        self._write_file('policies.rst', self._policy_rst(acct_configs))
        logger.info('Writing region list to regions.rst...')
        self._write_file('regions.rst', self._regions_rst())
        self._setup_mailer_templates()

    def _load_defaults(self):
        """
        Load a defaults.yml file from either the ``policies/`` subdirectory
        or directories in the ``policy_source_paths`` configuration key.
        """
        defaults = None
        # read the global defaults
        if os.path.exists(os.path.join('policies', 'defaults.yml')):
            defaults = self._read_file_yaml(
                os.path.join('policies', 'defaults.yml')
            )

        # check policy folders for defaults
        try:
            paths = self._config.policy_source_paths
            for path in paths:
                if os.path.exists(
                    os.path.join('policies', path, 'defaults.yml')
                ):
                    defaults = self._read_file_yaml(
                        os.path.join('policies', path, 'defaults.yml')
                    )
        except AttributeError:
            logger.debug("No additional source paths for defaults")
        return defaults

    def _load_all_policies(self):
        """
        Read the policies, either the current list of ``policy_source_paths``
        directories if the config key exists, or simply the ``policies/``
        subdirectory if it doesn't.
        """
        # dict to hold account_name -> config for that account
        acct_configs = {}
        try:
            logger.info(
                "Reading from multiple source paths: %s",
                self._config.policy_source_paths
            )
            for path in self._config.policy_source_paths:
                logger.info("Reading configs from %s", path)
                configs = self._load_policy(path=path)
                # update self._policy_sources to track where each policy was
                for aname, adata in configs.items():
                    for rname, rdata in adata.items():
                        for pname in rdata.keys():
                            self._policy_sources[pname].add(path)
                acct_configs = self._merge_configs(acct_configs, configs)
                logger.info(
                    "Merging configs from %s into existing configs", path
                )
        except AttributeError:
            logger.info(
                "No source paths defined, falling back to single source path"
            )
            acct_configs = self._load_policy()
        return acct_configs

    def _merge_configs(self, target, source):
        new_config = deepcopy(target)
        for acctname in source:
            if acctname in new_config:
                for region in source[acctname]:
                    if region in new_config[acctname]:
                        for rule in source[acctname][region]:
                            if rule in new_config[acctname][region]:
                                new_config[acctname][region][rule] \
                                    .update(source[acctname][region][rule])
                            else:
                                new_config[acctname][region][rule] = \
                                    deepcopy(source[acctname][region][rule])
                    else:
                        new_config[acctname][region] = \
                            deepcopy(source[acctname][region])
            else:
                new_config[acctname] = deepcopy(source[acctname])
        return new_config

    def _load_policy(self, path=''):
        """
        Load all policies in a given path; return a nested dict of account name
        (str) to region name (str) to dict of policy names (str) to policies
        (dict).

        :param path: path to load policies from
        :type path: str
        :return: nested dict of policies
        :rtype: dict
        """
        acct_configs = {}
        # read the shared configs from all_accounts/ ; returns a dict of
        # region name to [dict of policy name to policy], for each region
        all_accts = self._read_policy_directory(
            os.path.join(path, 'all_accounts')
        )
        # loop over all accounts in the config file
        for acctname in self._config.list_accounts(self._config.config_path):
            # start with the all_accts dict, for common config
            conf = deepcopy(all_accts)
            # read the account's config
            acct_conf = self._read_policy_directory(
                os.path.join(path, acctname)
            )
            # for each region, layer per-account over all_accounts
            for rname in self._config.regions:
                conf[rname].update(acct_conf[rname])
            acct_configs[acctname] = deepcopy(conf)
        return acct_configs

    def _read_policy_directory(self, policy_dir):
        """
        Read all policies from a ``policies/`` subdirectory (``all_accounts/``
        or an account name). Return a dict of region names to dict of policies
        (name to policy) for that region.

        :param policy_dir: ``policies/`` subdirectory name to read policies from
        :type policy_dir: str
        :return: dict of region name to policies dict (name to policy)
        :rtype: dict
        """
        common = self._read_policies(os.path.join(policy_dir, 'common'))
        region_policies = {}
        for rname in self._config.regions:
            policies = deepcopy(common)
            policies.update(
                self._read_policies(os.path.join(policy_dir, rname))
            )
            region_policies[rname] = policies
        return region_policies

    def _generate_configs(self, policies, defaults, region_name):
        """
        Given policies read from disk, apply defaults, generate cleanup
        policies, sanity/safety check policies. Then write the custodian configs
        to disk and return the resulting policies dict.

        :param policies: the policies read from disk (return value of
          :py:meth:`~._read_policies`)
        :type policies: dict
        :param defaults: the defaults to apply to the policies
        :type defaults: dict
        :param region_name: the name of the region these configs are for
        :type region_name: str
        :return: dictionary of final policies
        :rtype: dict
        """
        result = {'policies': []}
        for k in sorted(policies.keys()):
            result['policies'].append(
                self._apply_defaults(defaults, policies[k])
            )
        if self._config.cleanup_notify:
            logger.info('Generating c7n cleanup policies...')
            # add c7n lambda/CW Event cleanup policies
            for pol in self._generate_cleanup_policies(
                deepcopy(result['policies'])
            ):
                result['policies'].append(self._apply_defaults(defaults, pol))
        logger.info('Checking policies for sanity and safety...')
        self._check_policies(result['policies'])
        self._write_custodian_configs(result, region_name)
        return result

    def _write_custodian_configs(self, result, region_name):
        """
        Write the per-region ``custodian_REGION.yml`` config file to disk. This
        also handles ``%%`` macro and environment variable substitution.

        :param result: final custodian configuration
        :type result: dict
        :param region_name: the name of the region the configs are for
        :type region_name: str
        """
        config_str = yaml.dump(result)
        fname = 'custodian_%s.yml' % region_name
        logger.info('Writing %s policies to %s...' % (region_name, fname))
        conf = config_str
        replacements = [
            ['%%BUCKET_NAME%%', self._config.output_s3_bucket_name],
            ['%%LOG_GROUP%%', self._config.custodian_log_group],
            ['%%DLQ_ARN%%', self._config.dead_letter_queue_arn],
            ['%%ROLE_ARN%%', self._config.role_arn],
            ['%%MAILER_QUEUE_URL%%', self._config.mailer_config['queue_url']],
            ['%%ACCOUNT_NAME%%', self._config.account_name],
            ['%%ACCOUNT_ID%%', str(self._config.account_id)],
            ['%%AWS_REGION%%', region_name]
        ]
        for k, v in os.environ.items():
            if k.startswith('POLICYGEN_ENV_'):
                replacements.append(['%%' + k + '%%', v])
        for macro, val in replacements:
            conf = conf.replace(macro, val)
        self._write_file(fname, conf)

    def _check_policies(self, policies):
        """
        Check all of our policies to ensure that they conform with some rules
        and best practices around safety and sanity.

        Each policy in ``policies`` is passed through each of the
        ``self._check_policy_*`` functions (which return a boolean pass/fail).
        At the end, all failures are collected. If there are any, SystemExit(1)
        is raised.

        :param policies: list of policy dictionaries
        :type policies: list
        :raises: SystemExit(1) if any policies failed checks
        """
        policy_checks = []
        for x in dir(self):
            if x.startswith('_check_policy_') and callable(getattr(self, x)):
                policy_checks.append(getattr(self, x))
        failures = defaultdict(list)
        for pol in policies:
            for chk in policy_checks:
                if not chk(pol):
                    failures[pol['name']].append(strip_doc(chk))
        if len(failures) > 0:
            logger.error('ERROR: Some policies failed sanity/safety checks:')
            for pol_name in sorted(failures.keys()):
                logger.error(pol_name)
                for chk_str in failures[pol_name]:
                    logger.error("\t" + chk_str)
            raise SystemExit(1)
        logger.info('OK: All policies passed sanity/safety checks.')

    def _check_policy_marked_for_op_first(self, policy):
        """
        Policy includes a marked-for-op filter, but it is not the first filter.
        """
        if 'filters' not in policy:
            return True
        if "'type': 'marked-for-op'" not in str(policy['filters']):
            return True
        try:
            if policy['filters'][0].get('type', '') == 'marked-for-op':
                return True
        except AttributeError:
            # first filter isn't even a dict; that's a failure
            pass
        # fail - first filter isn't marked-for-op
        return False

    def _check_policy_mark_but_no_tag_filter(self, policy):
        """
        Policy performs a mark action, but does not filter out resources already
        marked with that tag.
        """
        if 'filters' not in policy:
            return True
        if 'actions' not in policy:
            return True
        mark_tags = []
        for a in policy['actions']:
            if not isinstance(a, type({})):
                # not a dict, can't be a mark action
                continue
            if a.get('type', '') != 'mark-for-op':
                continue
            mark_tags.append(a['tag'])
        for t in mark_tags:
            tag_filter = {'tag:%s' % t: 'absent'}
            if tag_filter not in policy['filters']:
                return False
        return True

    def _check_policy_mark_for_op_bad_message(self, policy):
        """
        mark-for-op action has message that does not end with
        ": {op}@{action_date}" (won't be parsed by c7n and will be ignored)
        """
        success = True
        if 'actions' not in policy:
            return True
        for a in policy['actions']:
            if not isinstance(a, type({})):
                # not a dict, can't be a mark action
                continue
            if a.get('type', '') != 'mark-for-op':
                continue
            if 'message' not in a:
                continue
            if not a['message'].endswith(': {op}@{action_date}'):
                success = False
        return success

    def _generate_cleanup_policies(self, policies):
        """
        When c7n is run, it provisions all policies as lambda functions. But if
        policies are removed, it doesn't know how to clean them up. See
        https://github.com/capitalone/cloud-custodian/issues/48

        As a workaround for this, we tag all Lambda funcs created by c7n
        with Project: cloud-custodian and a Component tag of the policy name.

        This method generates policies that look for cloud-custodian Lambda
        functions and CloudWatch Events that aren't in the current list of
        policies, and therefore probably need cleanup, and notifies us.

        :param policies: list of policy dictionaries
        :type policies: list
        :return: list of c7n cleanup policies to add
        :rtype: list
        """
        # base policies that just need filters added
        lcleanup = {
            'name': 'c7n-cleanup-lambda',
            'comment': 'Find and alert on orphaned c7n Lambda functions',
            'resource': 'lambda',
            'actions': [{
                'type': 'notify',
                'violation_desc': 'The following cloud-custodian Lambda '
                                  'functions appear to be orphaned',
                'action_desc': 'and should probably be deleted',
                'subject': '[cloud-custodian {{ account }}] Orphaned '
                           'cloud-custodian Lambda funcs in {{ region }}',
                'to': self._config.cleanup_notify,
            }],
            'filters': [
                {'tag:Project': 'cloud-custodian'},
                {'tag:Component': 'present'},
                # exclude itself...
                {
                    'type': 'value',
                    'key': 'tag:Component',
                    'op': 'ne',
                    'value': 'c7n-cleanup-lambda'
                },
                {
                    'type': 'value',
                    'key': 'tag:Component',
                    'op': 'ne',
                    'value': 'c7n-cleanup-cwe'
                }
            ]
        }
        cwecleanup = {
            'name': 'c7n-cleanup-cwe',
            'comment': 'Find and alert on orphaned c7n CloudWatch Events',
            'resource': 'event-rule',
            'actions': [{
                'type': 'notify',
                'violation_desc': 'The following cloud-custodian CloudWatch '
                                  'Event rules appear to be orphaned',
                'action_desc': 'and should probably be deleted',
                'subject': '[cloud-custodian {{ account }}] Orphaned '
                           'cloud-custodian CW Event rules in {{ region }}',
                'to': self._config.cleanup_notify,
            }],
            'filters': [
                {
                    'type': 'value',
                    'key': 'Name',
                    'op': 'glob',
                    'value': 'custodian-*'
                },
                # exclude itself...
                {
                    'type': 'value',
                    'key': 'Name',
                    'op': 'ne',
                    'value': 'custodian-c7n-cleanup-lambda'
                },
                {
                    'type': 'value',
                    'key': 'Name',
                    'op': 'ne',
                    'value': 'custodian-c7n-cleanup-cwe'
                }
            ]
        }
        # add the filters
        for p in policies:
            name = p['name']
            cwecleanup['filters'].append({
                'type': 'value',
                'key': 'Name',
                'op': 'ne',
                'value': 'custodian-%s' % name
            })
            lcleanup['filters'].append({
                'type': 'value',
                'key': 'tag:Component',
                'op': 'ne',
                'value': name
            })
        return [lcleanup, cwecleanup]

    def _write_file(self, path, content):
        """write a file - helper to make unit tests simpler"""
        with open(path, 'w') as fh:
            fh.write(content)

    def _apply_defaults(self, defaults, policy):
        d = deepcopy(defaults)
        conf = self._merge_conf(d, policy, policy['name'], [])
        # set Lambda func 'Component' tag to the policy name
        if conf['mode']['type'] == 'periodic' and 'tags' not in conf['mode']:
            conf['mode']['tags'] = {}
        if 'tags' in conf['mode']:
            conf['mode']['tags'].update(
                defaults.get('mode', {}).get('tags', {})
            )
            conf['mode']['tags']['Component'] = policy['name']
        if 'actions' not in conf:
            conf['actions'] = []
        return self._add_always_notify(conf)

    def _add_always_notify(self, conf):
        """
        Given a policy configuration like the one returned by
        :py:meth:`~._apply_defaults`, return the input unchanged if the
        ``always_notify`` configuration value is empty or not present, or else
        ensure that the policy contains at least one ``type: notify`` action
        with the specified transport and ``to``.

        :param conf: configuration as returned by :py:meth:`~._apply_defaults`
        :type conf: dict
        :return: conf with always_notify action if configured
        :rtype: dict
        """
        try:
            desired = self._config.always_notify
            desired['type'] = 'notify'
        except AttributeError:
            return conf
        added = False
        for action in conf['actions']:
            if not isinstance(action, type({})):
                continue
            if action.get('type', None) != 'notify':
                continue
            if action.get('transport', {}) != desired['transport']:
                continue
            # ok, we've got an action with the desired transport
            if 'to' not in action:
                action['to'] = []
            for to_addr in desired['to']:
                if to_addr not in action['to']:
                    action['to'].append(to_addr)
            added = True
            break
        if not added:
            conf['actions'].append(desired)
        return conf

    def _merge_conf(self, base, update, policy_name, path):
        """merge update into base"""
        for k, v in update.items():
            kpath = path + [k]
            if (
                kpath == ['mode'] and v.get('type', 'periodic') != 'periodic'
            ):
                # short-circuit to not alter the 'mode' top-level key on
                # policies if it isn't "type: periodic"
                base[k] = update[k]
                continue
            if k not in base:
                base[k] = v
                continue
            if isinstance(v, type([])):
                # List / array
                base[k] = self._array_merge(base[k], v, policy_name, kpath)
            elif isinstance(v, type({})):
                # nested dictionary
                base[k] = self._merge_conf(base[k], v, policy_name, kpath)
            else:
                # not a dict or list; probably string or int, etc.
                base[k] = v
        # remove actions if only specified in base (defaults)
        if path == [] and 'actions' in base and 'actions' not in update:
            del base['actions']
        return base

    def _array_merge(self, base, update, policy_name, path):
        """this starts with update, and adds things from base"""
        if not isinstance(base, type([])):
            logger.error(
                'ERROR: policy has an array but defaults does not; cannot merge'
            )
            raise RuntimeError(
                'Policy %s: Cannot array merge non-array from defaults (%s)' % (
                    policy_name, base
                )
            )
        # find the defaults, by type
        def_dicts = {}
        for v in base:
            # coverage doesn't report correctly on this branch
            if not isinstance(v, type({})):
                if v not in update:  # nocoverage
                    update.append(v)  # nocoverage
                continue  # nocoverage
            t = v.get('type', None)
            if t is None:
                raise RuntimeError('Do not know how to handle a defaults '
                                   'dict without a "type" key.')
            if t in def_dicts:
                raise RuntimeError('Defaults cannot specify multiple dicts '
                                   'with the same "type" in the same array!')
            def_dicts[t] = v
        # do the updates
        for i in update:
            if not isinstance(i, type({})):
                continue
            # else it's a dict, update from defaults if present
            t = i.get('type', None)
            if t is None:
                continue
            if t not in def_dicts:
                # no defaults for this
                continue
            for k, v in def_dicts[t].items():
                if k not in i:
                    i[k] = v
            del def_dicts[t]
        # add any defaults that didn't already exist
        for k, v in def_dicts.items():
            if path == ['actions'] and k == 'notify':
                # Don't add notify actions to policies that don't have them
                continue
            update.append(v)
        return update

    def _policy_rst(self, region_policies):
        """
        Build the policies rST source for the documentation.

        :param region_policies: dict of region names to per-region dict of
          policy name to policy content, for that region.
        :type region_policies: dict
        :return: built rST markup for policies docs
        :rtype: str
        """
        buildinfo = 'by `%s %s <%s>`_' % (
            os.environ.get('JOB_NAME', ''),
            os.environ.get('BUILD_NUMBER', ''),
            os.environ.get('BUILD_URL', '')
        )
        commit = os.environ.get('GIT_COMMIT', 'unknown')
        gitlink = '%scommit/%s' % (git_html_url(), commit)
        if buildinfo == 'by `  <>`_':
            buildinfo = 'locally'
        s = "this page built %s from `%s <%s>`_ at %s\n\n" % (
            buildinfo, commit, gitlink, timestr()
        )
        try:
            assert len(self._config.policy_source_paths) > 0
            headers = [
                'Policy Name', 'Account(s) / Region(s)', 'Source Path(s)',
                'Description/Comment'
            ]
            have_source_paths = True
        except Exception:
            headers = [
                'Policy Name', 'Account(s) / Region(s)', 'Description/Comment'
            ]
            have_source_paths = False
        s += tabulate(
            sorted(self._policy_rst_data(
                region_policies, have_paths=have_source_paths
            )),
            headers=headers, tablefmt='grid'
        )
        return s

    def _policy_rst_data(self, account_policies, have_paths=False):
        """
        Build the policy rST table data.

        :param account_policies: dict of Account names to dict of [region names
          to per-region dict of policy name to policy content].
        :type account_policies: dict
        :return: list of [name, regions, comment] lists for each policy
        :rtype: ``list``
        """
        all_regions = sorted(self._config.regions)
        acct_names = sorted(account_policies.keys())
        names_to_accts_regions = {
            x: defaultdict(list) for x in account_policies.keys()
        }
        descriptions = {}
        for acctname in sorted(account_policies.keys()):
            region_policies = account_policies[acctname]
            for rname in sorted(region_policies.keys()):
                policies = region_policies[rname]
                for pname in sorted(policies.keys()):
                    names_to_accts_regions[acctname][pname].append(rname)
                    descriptions[pname] = self._policy_comment(policies[pname])
        result = []
        for pname in sorted(descriptions.keys()):
            accts = []
            for acctname in acct_names:
                regions = sorted(names_to_accts_regions[acctname][pname])
                if regions == all_regions:
                    accts.append(acctname)
                elif len(regions) > 0:
                    accts.append('%s (%s)' % (
                        acctname, ' '.join(regions)
                    ))
            if accts == acct_names:
                apart = ''
            else:
                apart = ' '.join(accts)
            if have_paths:
                result.append([
                    pname,
                    apart,
                    ' '.join(sorted(self._policy_sources.get(pname, []))),
                    descriptions[pname]
                ])
            else:
                result.append([
                    pname,
                    apart,
                    descriptions[pname]
                ])
        return result

    def _regions_rst(self):
        res = ''
        for acctname in self._config.list_accounts(self._config.config_path):
            aconf = self._config.from_file(self._config.config_path, acctname)
            res += '  * %s (%s)\n\n' % (acctname, aconf.account_id)
            res += "\n".join(['    * %s' % r for r in aconf.regions]) + "\n\n"
        return res

    def _policy_comment(self, policy):
        for k in ['comment', 'comments', 'description']:
            if k in policy:
                return policy[k].strip()
        return 'unknown'

    def _read_policies(self, subdir):
        """
        Read policy files from a subdirectory of the policies directory, and
        return the resulting dict of policy names to policy contents.

        :param subdir: directory path under ``policies/`` to read
        :type subdir: str
        :return: dict of policy names to policies
        :rtype: dict
        """
        res = {}
        try:
            for f in os.listdir(os.path.join('policies', subdir)):
                if not f.endswith('.yml'):
                    continue
                name = f.split('.')[0]
                y = self._read_file_yaml(os.path.join('policies', subdir, f))
                res[name] = y
                if name != 'defaults' and y.get('name', '') != name:
                    raise RuntimeError(
                        'ERROR: Policy file %s contains policy with name '
                        '"%s".' % (f, y.get('name', ''))
                    )
        except OSError:
            return {}
        logger.info(
            'Loaded %d policies from %s: %s', len(res), subdir, res.keys()
        )
        return res

    def _read_file_yaml(self, path):
        """unit test helper - return YAML from file contents"""
        with open(path, 'r') as fh:
            contents = fh.read()
        try:
            return yaml.load(contents, Loader=SafeLoader)
        except Exception:
            sys.stderr.write("Exception loading YAML: %s\n" % path)
            raise

    def _setup_mailer_templates(self):
        """
        Call :py:meth:`~._mailer_template_paths`. If it returns an empty dict,
        do nothing. Otherwise, create ``./mailer-templates`` if it does not
        already exist. For each template filename that does not already exist
        in that directory, copy it from the source path specified by
        :py:meth:`~._mailer_template_paths`.
        """
        paths = self._mailer_template_paths()
        if not paths:
            logger.info(
                'No mailer-templates directories found in policy_source_paths; '
                'not setting up mailer templates.'
            )
            return
        if not os.path.exists('mailer-templates'):
            logger.info('Creating directory: mailer-templates')
            os.mkdir('mailer-templates')
        for fname, srcpath in paths.items():
            destpath = os.path.join('mailer-templates', fname)
            if os.path.exists(destpath):
                logger.info(
                    '%s already exists in pwd; not overwriting', destpath
                )
            else:
                logger.info(
                    'Setting up %s from source at %s', destpath, srcpath
                )
                shutil.copyfile(srcpath, destpath)
        logger.info('Done setting up mailer-templates')

    def _mailer_template_paths(self):
        """
        Find all files in the ``mailer-templates`` subdirectory of each
        ``policy_source_paths`` directory, if present. Return a dictionary of
        file name to file path. If a file with the same name is found in
        multiple directories, the last one in ``policy_source_paths`` order
        wins.

        :return: Mailer template names to their source paths
        :rtype: dict
        """
        templates = {}
        try:
            logger.debug(
                "Finding mailer-templates in: %s",
                self._config.policy_source_paths
            )
            for path in self._config.policy_source_paths:
                mailerdir = os.path.join('policies', path, 'mailer-templates')
                if not os.path.exists(mailerdir):
                    logger.debug('%s does not exist; skipping', mailerdir)
                    continue
                logger.info('Finding mailer templates in %s', mailerdir)
                for f in os.listdir(mailerdir):
                    fpath = os.path.join(mailerdir, f)
                    if not os.path.isfile(fpath):
                        continue
                    logger.debug(
                        'Using mailer template %s from %s', f, fpath
                    )
                    templates[f] = fpath
        except AttributeError:
            logger.debug(
                "No policy_source_paths defined; not setting up "
                "mailer-templates."
            )
        return templates


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

    p = argparse.ArgumentParser(
        description='Tool to generate custodian config files '
                    'from a c7n configuration directory/repo.',
        epilog='This tool is part of manheim_c7n_tools v%s.\n'
               'For documentation, see: %s' % (VERSION, PROJECT_URL),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument('-V', '--version', action='version', version=VERSION)
    p.add_argument('-c', '--config', dest='config', action='store',
                   default='manheim-c7n-tools.yml',
                   help='Config file path (default: ./manheim-c7n-tools.yml)')
    p.add_argument('ACCT_NAME', action='store', type=str,
                   help='account_name value from config file, for '
                        'current account')

    args = p.parse_args(sys.argv[1:])
    conf = ManheimConfig.from_file(args.config, args.ACCT_NAME)
    PolicyGen(conf).run()


if __name__ == "__main__":
    main()
