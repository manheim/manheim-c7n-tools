.. _`dryrun-diff`:

===========
Dryrun-Diff
===========

:py:mod:`Source code docs <manheim_c7n_tools.dryrun_diff>`.

The ``dryrun-diff`` entrypoint (and corresponding ``manheim-c7n-tools`` step) must be run in a directory containing the ``dryrun/`` output directory from a custodian dry run. It parses the resource counts for each policy executed in each region during the dry run, then retrieves the logs from the last actual custodian run from S3. The matched resource counts are compared, and a markdown file is generated for use as a GitHub PR comment. This allows us to compare the impact of policy change pull requests.

The generated markdown file will be written to ``./pr_diff.md`` in the current directory.
