.. _`dryrun-diff`:

===========
Dryrun-Diff
===========

:py:mod:`Source code docs <manheim_c7n_tools.dryrun_diff>`.

The ``dryrun-diff`` entrypoint (and corresponding ``manheim-c7n-tools`` step) must be run after the custodian dry run step is completed in all regions. It parses the resource counts for each policy executed in each region during the dry run (from the ``dryrun/`` output directory), then retrieves the logs from the last actual custodian run from S3. The matched resource counts are compared, and a markdown file is generated for use as a GitHub PR comment. This allows us to compare the impact of policy change pull requests.

The generated markdown file will be written to ``./pr_diff.md`` in the current directory.

Note: ``dryrun-diff`` will ONLY show changes to resource counts. Updated policies (comment updates, etc.) will not show up in the ``dryrun-diff`` unless resource counts are changing.

If the ``dryrun-diff`` entrypoint has been run in a directory containing a jinja template located at ``./reporting-template/report.j2``, this template will be used to generate a detailed HTML report of which resources have been affected by policy changes. An example of a reporting jinja template can be found within the ``./example_config_repo`` folder at the root of the Manheim repository. The report will written to ``./pr_report.html`` in the current directory.