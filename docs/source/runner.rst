.. _`runner`:

==================
manheim-c7n-runner
==================

This provides a single command-line script/entrypoint to run some or all of the commands required to deploy our custodian infrastructure in the correct order. It supports either normal or dryrun mode. The full list of steps run, in order, is:

- :ref:`policygen.py <policygen>`
- c7n config validation
- :py:mod:`mugc <manheim_c7n_tools.vendor.mugc>`
- custodian run or dry-run
- c7n-mailer deploy or validate (dry-run)
- :ref:`dryrun-diff`
- :ref:`s3archiver`
- Sphinx docs build (HTML listing of policies by account/region)

The wrapper runs for one account at a time, and the account name (matching one in the configuration file) must be specified on the command line. See ``manheim-c7n-runner accounts`` to list configured accounts.

See ``manheim-c7n-runner --help`` in the Docker image for usage information. You can run all steps, or select only a subset of steps to include or exclude, in normal or dry-run mode.

.. _runner.running_locally:

Running Locally
---------------

To perform a dry-run of Custodian policies locally via the Docker image, run the following command from your custodian configuration repository. This will mount your current directory into the container, and use the policies from this directory.

.. code-block:: shell

    docker run -it --rm \
      -v $(pwd):/configs \
      --workdir /configs \
      -e "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" \
      -e "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" \
      -e "AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN" \
      manheim/manheim-c7n-tools:latest \
      manheim-c7n-runner -r $AWS_REGION -v --no-assume-role \
      --step=policygen --step=validate --step=custodian dryrun ACCOUNT-NAME

This assumes that you have valid AWS credentials exported in your current environment for the desired account (``ACCOUNT-NAME``).

In some cases, you may need to add additional components to this command:

* If any of your policies or configuration files include ``POLICYGEN_ENV_`` interpolation via :ref:`policies.region_interpolation`, you must also export the relevant environment variables for those interpolations.
* If you have custom c7n-mailer templates (e.g. in a ``mailer-templates/`` directory in your configuration repository), you should mount in that directory (e.g. ``-v $(pwd)/mailer-templates:/manheim_c7n_tools/manheim_c7n_tools/mailer-templates``).

.. _runner.multi-account:

Multi-Account Support
---------------------

``manheim-c7n-tools`` supports configuration for multiple accounts. Most ``manheim-c7n-runner`` subcommands (``run`` and ``dryrun``) require an account name to be specified, to run against. The command can only run against one account at a time. Our :ref:`policies.repo_layout` supports policies both shared between all accounts and specific to a single account. Accounts must be configured individually in the configuration file (see below).

See ``manheim-c7n-runner accounts`` to list configured accounts.

Running cross-account (i.e. from Jenkins) is supported by configuring a role to assume in the ``manheim-c7n-tools.yml`` configuration file. There is an optional top-level ``assume_role`` key under each account, the value of which is a hash/dict with the following keys:

* ``role_arn`` - **required**, the ARN of the role to assume in another account
* ``external_id`` - *optional*, an External ID string to pass when assuming the role
* ``duration_seconds`` - *optional*, an integer number of seconds for the assumed role credentials to be valid, from 900 to 43200 seconds (default 3600)

If you are running locally and don't have to assume a role because you have credentials for the destination account already set, use the ``-A`` / ``--no-assume-role`` option to skip assuming a role.
