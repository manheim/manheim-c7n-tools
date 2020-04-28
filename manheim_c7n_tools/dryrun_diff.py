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
Script to compare the affected resources matched per-policy, per-region
between a dryrun and the last actual run of each policy. High-level results
are written to a Mardown file (to be added as a comment on the PR), Low-level
differences are written to a HTML file (to be added as a link on the PR).
"""

import sys
import glob
import re
import logging
import json
import boto3
import argparse
import itertools
from zlib import decompress
import subprocess
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound

from c7n.resources import load_available
from c7n.provider import get_resource_class

from manheim_c7n_tools.utils import set_log_info, set_log_debug
from manheim_c7n_tools.config import ManheimConfig
from manheim_c7n_tools.version import VERSION

logger = logging.getLogger(__name__)


class DryRunDiffer(object):

    def __init__(self, config):
        """
        Initialize a dryrun differ.

        :param config: manheim-c7n-tools configuration object
        :type config: ManheimConfig
        """
        self._live_results = {}
        self.config = config

    def run(self, git_dir=None, diff_against='master'):
        changed_policies = self._find_changed_policies(git_dir, diff_against)
        if len(changed_policies) == 0:
            logger.info(
                'Git diff did not report any changed policies; skipping '
                'resource count diff.'
            )
            with open('pr_diff.md', 'w') as fh:
                fh.write('Git diff did not report any changed policies; '
                         'skipping resource count diff.')
            return
        logger.info('Changed policies for diff: %s', changed_policies)
        dryrun_results = self._get_dryrun_results(changed_policies)
        logger.info('Reading results from last run from S3')
        for rname in self.config.regions:
            logger.debug('Getting S3 results for region: %s', rname)
            self._get_s3_results_for_region(rname, changed_policies)
        diff_md = self._make_diff_markdown(dryrun_results)
        with open('pr_diff.md', 'w') as fh:
            if 'defaults' in changed_policies:
                fh.write(
                    'PR found to contain changes to defaults.yml and '
                    '%d other policies\n\n' % (len(changed_policies) - 1)
                )
            else:
                fh.write(
                    'PR found to contain changes to '
                    '%d policies\n\n' % len(changed_policies)
                )
            fh.write(diff_md)
        logger.info('PR diff written to: pr_diff.md')
        diff_report = self._make_diff_report(dryrun_results)
        if diff_report:
            with open('pr_report.html', 'w') as fh:
                fh.write(diff_report)
            logger.info('PR report written to: pr_report.html')

    def _find_changed_policies(self, git_dir=None, diff_against='master'):
        """
        :return: list of policy names that differ from master
        :rtype: list
        """
        res = subprocess.check_output(
            ['git', 'diff', '--name-only', diff_against],
            cwd=git_dir
        ).decode().split("\n")
        pnames = []
        polname_re = re.compile(r'^policies.*/([a-zA-Z0-9_-]+)\.yml$')
        for x in res:
            x = x.strip()
            if x == '':
                continue
            m = polname_re.match(x)
            if not m:
                continue
            pnames.append(m.group(1))
        return pnames

    def _make_diff_report(self, dryrun):
        """
        Return a HTML report breaking down the differences between the dryrun
        (this branch) and the last run of each policy on master.

        Requires a jinja template located at `./reporting-template/report.j2`
        within the same directory where the dryrun-diff step has been run.

        :param dryrun: dryrun policy resource information
        :type dryrun: dict
        :return: html report
        :rtype: str
        """
        all_policies = list(
            set(dryrun.keys()) | set(self._live_results.keys())
        )
        entries = {}
        if not all_policies:
            logger.info('no policies found - skipping diff report')
            return ''
        t_loader = FileSystemLoader(searchpath="./reporting-template/")
        t_env = Environment(loader=t_loader)
        t_file = "report.j2"
        try:
            tmpl = t_env.get_template(t_file)
        except TemplateNotFound:
            logger.info('unable to find a template - skipping diff report')
            return ''

        for policy in all_policies:
            policy_splits = policy.split('-', 1)
            if len(policy_splits) <= 1:
                logger.warning(
                    "skipping policy: \
                        %s from report - it is not prefixed correctly",
                    policy)
                continue
            resource_type = policy_splits[0]
            load_available()
            _id = get_resource_class(resource_type) \
                .resource_type() \
                .id
            for region in self.config.regions:
                dry_ids = {
                    '{}: {}'.format(_id, x[_id])
                    for x in dryrun.get(policy, {}).get(region, [])
                }
                live_ids = {
                    '{}: {}'.format(_id, x[_id])
                    for x in self._live_results.get(policy, {}).get(region, [])
                }
                additions = [
                    {'id': x, 'type': 'added'}
                    for x in dry_ids.difference(live_ids)
                ]
                removals = [
                    {'id': x, 'type': 'removed'}
                    for x in live_ids.difference(dry_ids)
                ]
                untouched = [
                    {'id': x, 'type': 'unchanged'}
                    for x in dry_ids.intersection(live_ids)
                ]
                resources = list(itertools.chain.from_iterable((
                    additions or [],
                    removals or [],
                    untouched or []
                )))
                if policy not in entries:
                    entries[policy] = {}
                entries[policy][region] = {
                    'resources': resources,
                    'total_add': len(additions),
                    'total_remove': len(removals),
                    'total_untouch': len(untouched)
                }
        return tmpl.render(
            account_name=self.config.account_id,
            entries=entries
        )

    def _make_diff_markdown(self, dryrun):
        """
        Return GitHub-flavored Markdown showing the difference between the
        dryrun (this branch) and the last run of each policy on master.

        :param dryrun: dryrun policy resource counts
        :type dryrun: dict
        :return: markdown diff
        :rtype: str
        """
        all_policies = list(set(
            list(dryrun.keys()) + list(self._live_results.keys())
        ))
        if len(all_policies) == 0:
            return 'No policy reports found. Perhaps all changed policies ' \
                   'are event-based instead of periodic?\n'
        maxlen = max([len(x) for x in all_policies])
        fmt = '%s %{maxlen}s   %6s   %6s   %6s   \n'.format(maxlen=maxlen)
        linelen = 30 + maxlen
        res = '```diff\n'
        res += '##%s    last                  ##\n' % (' ' * maxlen)
        res += '##%s    live                  ##\n' % (' ' * maxlen)
        res += '##%s    run       PR    diff  ##\n' % (' ' * maxlen)
        for pname in sorted(all_policies):
            res += '%s\n' % ('=' * linelen)
            res += pname + "\n"
            for rname in self.config.regions:
                a = len(self._live_results.get(pname, {}).get(rname, []))
                b = len(dryrun.get(pname, {}).get(rname, []))
                a_str = '--' if a == 0 else a
                b_str = '--' if b == 0 else b
                prefix = ' '
                diff = ''
                if a == '--' and b != '--':
                    # in PR but not in master/live
                    prefix = '+'
                    diff = '+%d' % b
                elif a != '--' and b == '--':
                    # in master/live but not in PR
                    prefix = '-'
                    diff = -1 * a
                if a > b:
                    # in both, more resources in live than PR
                    prefix = '-'
                    diff = b - a
                elif a < b:
                    # in both, fewer resources in live than PR
                    prefix = '+'
                    diff = b - a
                res += fmt % (
                    prefix, rname, a_str, b_str, diff
                )
        res += '```\n'
        return res

    def _get_dryrun_results(self, pol_names):
        """
        Read the `resources.json` files from disk for the dryrun/ directory.
        Return a dictionary of string policy name to nested dictionaries, of
        string region name to resources.

        :return: dictionary of nested dictionaries, policy name to dict of
          region name to resource
        :rtype: dict
        """
        res = {}
        logger.debug('Getting dryrun results from disk...')
        fname_re = re.compile(r'dryrun/([^/]+)/([^/]+)/resources.json')
        for f in glob.glob('dryrun/*/*/resources.json'):
            m = fname_re.match(f)
            if not m:
                logger.error('ERROR: file path does not match regex: %s', f)
                continue
            region = m.group(1)
            policy = m.group(2)
            if policy not in pol_names and 'defaults' not in pol_names:
                # policy isn't changed
                continue
            logger.debug('Reading file: %s', f)
            if policy not in res:
                res[policy] = {}
            try:
                with open(f, 'r') as fh:
                    resources = json.loads(fh.read())
            except Exception:
                logger.error('ERROR reading file: %s', f, exc_info=True)
                continue
            res[policy][region] = resources
        logger.debug('Got dryrun results for %d policies', len(res))
        return res

    def _get_s3_results_for_region(self, region_name, changed_pols):
        """
        Find the results files in S3 from the last live run of the deployed
        policies. Reads each file and maps resources to ``self._live_results``
        accordingly.
        """
        s3 = boto3.resource('s3', region_name=region_name)
        bktname = self.config.config_for_region(
            region_name
        ).output_s3_bucket_name
        bkt = s3.Bucket(bktname)
        prefixes = self._get_s3_policy_prefixes(bkt)
        logger.debug('Found %d policy prefixes in %s', len(prefixes), bktname)
        for p in prefixes:
            if p not in changed_pols and 'defaults' not in changed_pols:
                # policy was not changed, skip it
                continue
            if p not in self._live_results:
                self._live_results[p] = {}
            self._live_results[p][region_name] = \
                self._get_latest_res_for_policy(bkt, p)
        logger.debug('Done getting resource counts for %s', region_name)

    def _get_s3_policy_prefixes(self, bucket):
        """
        Find all of the per-policy prefixes (a.k.a. "directories") in the S3
        bucket. Return a list of them

        :param bucket: the S3 bucket to list policies in
        :type bucket: ``boto3.S3.Bucket``
        :return: list of per-policy prefixes in S3 bucket
        :rtype: list
        """
        client = bucket.meta.client
        response = client.list_objects(
            Bucket=bucket.name,
            Delimiter='/',
            Prefix='logs/'
        )
        if response['IsTruncated']:
            raise RuntimeError('ERROR: S3 response was truncated!')
        if 'CommonPrefixes' not in response:
            logger.error(
                'ERROR: "CommonPrefixes" element not in S3 ListObjects '
                'response; bucket must be empty!'
            )
            return []
        result = []
        for pname in response['CommonPrefixes']:
            result.append(pname['Prefix'].replace('logs/', '').strip('/'))
        return result

    def _get_latest_res_for_policy(self, bucket, pol_name):
        """
        Given the S3 Bucket and a policy name, find the newest
        ``resources.json`` file for that policy and return the count of
        resources in it.

        :param bucket: the bucket to look in
        :type bucket: ``boto3.S3.Bucket``
        :param pol_name: the name of the policy
        :type pol_name: str
        :return: resource count from latest run of the policy
        :rtype: int
        """
        newest = None
        for obj in bucket.objects.filter(Prefix='logs/%s/' % pol_name):
            if not (
                obj.key.endswith('/resources.json') or
                obj.key.endswith('/resources.json.gz')
            ):
                continue
            if newest is None or obj.last_modified > newest.last_modified:
                newest = obj
        if newest is None:
            logger.warning('Found no resources.json objects for %s', pol_name)
            return 0
        logger.debug('Found newest key for %s in %s: %s', pol_name, bucket.name,
                     newest.key)
        # ok, ``newest`` is the newest resource.json for the policy; read it
        res = newest.get()
        body = res['Body']
        if newest.key.endswith('.gz'):
            # object is gzipped; see c7n.output.FSOutput.compress()
            body = body.read()
            body = decompress(body, 15 + 32)
        resources = json.loads(body)
        return resources


def parse_args(argv):
    p = argparse.ArgumentParser(
        description='Generate a diff of resources matched by policies in '
                    'this dryrun vs the live policies'
    )
    p.add_argument('-V', '--version', action='version', version=VERSION)
    p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-g', '--git-dir', dest='git_dir', action='store', type=str,
                   default=None, help='path to git directory, if not pwd')
    p.add_argument('-d', '--diff-against', dest='diff_against', action='store',
                   type=str, default='master',
                   help='git ref to diff against (default: master)')
    p.add_argument('-c', '--config', dest='config', action='store',
                   default='manheim-c7n-tools.yml',
                   help='Config file path (default: ./manheim-c7n-tools.yml)')
    p.add_argument('ACCOUNT_NAME', type=str, action='store',
                   help='Account name in config file, to run diff for')
    args = p.parse_args(argv)
    return args


def main():
    global logger
    # setup logging for direct command-line use
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
    # end setup logging

    args = parse_args(sys.argv[1:])

    # set logging level
    if args.verbose > 1:
        set_log_debug(logger)
    elif args.verbose == 1:
        set_log_info(logger)

    conf = ManheimConfig.from_file(args.config, args.ACCOUNT_NAME)
    DryRunDiffer(conf).run(
        git_dir=args.git_dir,
        diff_against=args.diff_against,
    )


if __name__ == "__main__":
    main()
