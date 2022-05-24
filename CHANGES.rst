Changelog
=========

1.4.3 (2022-05-24)
------------------

* Bump c7n to release 0.9.16
* Bump c7n-mailer to release 0.6.15 
* Update sphinx dependencies to 4.x

1.4.2 (2022-05-20)
------------------

* Bump c7n to release 0.9.16
* Bump c7n-mailer to release 0.6.15

1.4.1 (2022-02-09)
------------------

* Fixes `#67 <https://github.com/manheim/manheim-c7n-tools/issues/67>`__ - Add ``check_deprecations="yes"`` for Validate stage


1.4.0 (2022-01-20)
------------------

* Bump c7n to release 0.9.14
* Bump c7n-mailer to release 0.6.13
* Updated dependencies for c7n and c7n-mailer
  * Remove version contstrains for ``docutils``
  * Pin ``mistune==0.8.4`` for docs
* Replace TravisCI with Github Actions


1.3.1 (2021-06-14)
------------------

* Fixing dryrun-diff bug to show changes to inherited policies.
   * Remove `git diff` comparison; Now we compare results of full dryrun to last live-run

1.3.0 (2021-01-13)
------------------

* Fixes `#56 <https://github.com/manheim/manheim-c7n-tools/issues/56>`__ - Bump c7n version from 0.9.4 to `0.9.10 <https://github.com/cloud-custodian/cloud-custodian/releases/tag/0.9.10.0>`__ and c7n-mailer from 0.6.3 to 0.6.9.
* Bump relax boto3 and botocore dependencies to work with c7n and new pip resolver.
* Add testing under Python 3.9; switch default Python version for tox/TravisCI to 3.9.
* Bump base Docker image to latest ``python:3.9.1-alpine3.12``
* Implement :ref:`policies.notify_only`.
* Fix failing test.

1.2.4 (2020-07-29)
------------------

* Fixes `#53 <https://github.com/manheim/manheim-c7n-tools/issues/53>`__

  * Add ``function_prefix`` option to ``manheim-c7n-tools.yml`` to allow passing this option to mugc. Default it to the current/default ``custodian-``.
  * Have :py:class:`~.runner.MugcStep` use configured ``function_prefix`` instead of hard-coded ``custodian-``.
  * New policy sanity check :py:meth:`~.PolicyGen._check_policy_function_prefix` - fail if a policy's ``function-prefix`` doesn't match the configured (``manheim-c7n-tools.yml``) ``function_prefix``.

* Switch from deprecated pep8 / pytest-pep8 to pycodestyle / pytest-pycodestyle.

1.2.3 (2020-07-10)
------------------

* Update policygen to add enabled/disabled status to generated policy documentation

1.2.2 (2020-07-08)
------------------

* Bump c7n to release 0.9.4
* Bump c7n-mailer to release 0.6.3
* Updated dependencies for c7n and c7n-mailer

1.2.1 (2020-06-25)
------------------

* Bump c7n and c7n-mailer installed version to `26ba07e <https://github.com/cloud-custodian/cloud-custodian/commit/26ba07ea569dfe320682f7509082fc9bead0ca4c>`__ in order to pull in `PR #5893 <https://github.com/cloud-custodian/cloud-custodian/pull/5893>`__, fix for `#5854 <https://github.com/cloud-custodian/cloud-custodian/issues/5854>`__ c7n config splunk sourcetype.
* Bump c7n and c7n-mailer versions in setup.py to match the latest versions released

1.2.0 (2020-06-22)
------------------

* Add a new ``disable`` option for rules to disable rules from parent rulesets
* Fix bug in rule overriding where rules with the same names were merged rather than the later rule completely overriding the older one

1.1.0 (2020-06-10)
------------------

* Add documentation on how to run ``c7n-mailer-replay``.
* Add ``-n`` / ``--never-match-re`` option to ``errorscan`` endpoint, to allow specifying a regex for log messages to never consider a failure/error.
* Bump c7n from `b62af99 <https://github.com/cloud-custodian/cloud-custodian/commit/b62af99171bf1163413d7f7411e4a0db8a50f27e>`__ (master after 0.9.1 plus some merged PRs) to the upstream `0.9.3 release <https://github.com/cloud-custodian/cloud-custodian/releases/tag/0.9.3.0>`__. This pulls in changes from the upstream `0.9.2.0 <https://github.com/cloud-custodian/cloud-custodian/releases/tag/0.9.2.0>`__ and `0.9.3.0 <https://github.com/cloud-custodian/cloud-custodian/releases/tag/0.9.3.0>`__ releases.
* Bump c7n-mailer from `b62af99 <https://github.com/cloud-custodian/cloud-custodian/commit/b62af99171bf1163413d7f7411e4a0db8a50f27e>`__ (master after 0.6.0 plus some merged PRs) to the upstream 0.6.2 release. This pulls in changes from the upstream `0.9.2.0 <https://github.com/cloud-custodian/cloud-custodian/releases/tag/0.9.2.0>`__ and `0.9.3.0 <https://github.com/cloud-custodian/cloud-custodian/releases/tag/0.9.3.0>`__ releases.

1.0.0 (2020-05-26)
------------------

* Merge `PR #34 <https://github.com/manheim/manheim-c7n-tools/pull/34>`__ to add an optional full HTML report to the ``dryrun-diff`` step/entrypoint, triggered by the presence of a ``reporting-template/report.j2`` template file. Many thanks to `@JuubiSnake <https://github.com/JuubiSnake>`__ of `FundingCircle <https://github.com/FundingCircle>`__ for the contribution.
* In recognition of this project being used extensively in our organization, bump version to 1.0.0.

0.10.3 (2020-05-12)
-------------------

* Bump c7n and c7n-mailer installed version to `b62af99 <https://github.com/cloud-custodian/cloud-custodian/commit/b62af99171bf1163413d7f7411e4a0db8a50f27e>`__ in order to pull in `PR #5751 <https://github.com/cloud-custodian/cloud-custodian/pull/5751>`__, fix for `#5750 <https://github.com/cloud-custodian/cloud-custodian/issues/5750>`__ c7n-mailer critical bug.
* Add unit test to ensure that the ``c7n-mailer`` Lambda package archive can be successfully generated.
* Add ``pip freeze`` to the end of Docker image tests, to keep a record of the packages installed in Docker in the build logs.

0.10.2 (2020-05-11)
-------------------

* Install c7n and c7n-mailer directly from github, instead of PyPI, to pull in unreleased-but-merged `b7178be <https://github.com/cloud-custodian/cloud-custodian/commit/b7178be718bd8c8bdb70b2376d3bb0d5eb6fa9a9>`__ / `PR #5708 <https://github.com/cloud-custodian/cloud-custodian/pull/5708>`__ which fixes `Issue #5707 <https://github.com/cloud-custodian/cloud-custodian/issues/5707>`__ for missing ``jsonpointer`` and ``jsonpatch`` dependencies.
* Remove ``jsonpointer`` from requirements.
* Add ``libffi-dev`` and ``openssl-dev`` build dependencies to Dockerfile.
* Add ``.dockerignore`` file to make Docker builds more efficient.

0.10.1 (2020-05-08)
-------------------

* Add ``jsonpointer`` to requirements.

0.10.0 (2020-05-06)
-------------------

**Important:** In following upstream c7n's `0.9.1.0 release <https://github.com/cloud-custodian/cloud-custodian/releases/tag/0.9.1.0>`__, this release drops support for Python 2.7. A modern version of Python 3 is now required.

* Upgrade `c7n-mailer <https://github.com/cloud-custodian/cloud-custodian/tree/master/tools/c7n_mailer>`__ requirement from 0.5.7 to 0.6.0.
* Upgrade ``c7n`` requirement from 0.8.46.0 to 0.9.1.0.
* Switch TravisCI tests from py36 and py37 to py37 and py38.
* Update vendored-in ``mugc`` with latest upstream version, for compatibility with above changes.

0.9.2 (2020-04-20)
------------------

* Add ``m2r`` package as dependency, for Sphinx docs builds.

0.9.1 (2020-04-20)
------------------

* If the ``policy_source_paths`` configuration option is specified, have policygen include a column showing which source(s) a policy came from in ``policies.rst``.
* Fix bug in ``dryrun-diff`` step where it would fail on an initial, empty S3 bucket.

0.9.0 (2020-04-08)
------------------

* Previously, manheim-c7n-tools set c7n-mailer's ``templates_folders`` configuration option to ``/manheim_c7n_tools/manheim_c7n_tools/mailer-templates`` if that directory exists, or to the absolute path to a ``mailer-templates`` directory inside the ``manheim_c7n_tools`` installation otherwise. This behavior was largely based on the legacy hard-coded templates directory. Now that c7n-mailer template locations are more flexible, this behavior has been updated to (in order of evaluation):

  * Use the ``templates_folders`` option from the ``mailer_config`` section of ``manheim-c7n-tools.yml``, if present. Otherwise, start with an empty list.
  * Prepend ``./mailer-templates`` if it exists.
  * Prepend ``/manheim_c7n_tools/manheim_c7n_tools/mailer-templates`` to the list, if it exists.
  * Prepend ``mailer-templates`` directory inside the ``manheim_c7n_tools`` installation, if it exists.

0.8.6 (2020-04-07)
------------------

* Fix bug in 0.8.5 - mailer template loading logic was missing ``policies/`` directory prefix.

0.8.5 (2020-04-06)
------------------

* Update ``policygen`` to also handle layering of ``mailer-templates`` directory contents from ``policy_source_paths`` into ``./mailer-templates``.
* Fixes `#23 <https://github.com/manheim/manheim-c7n-tools/issues/23>`_ - Document ``cleanup_notify`` config parameter in example ``manheim-c7n-tools.yml`` files and default it to an empty list.
* Fixes `#24 <https://github.com/manheim/manheim-c7n-tools/issues/24>`_ - Remove requirement that us-east-1 must be first configured region, or configured at all.

0.8.4 (2020-04-01)
------------------

* ``errorscan`` - Warn on missing SQS dead letter queue instead of failing, to support deployments that only run mailer in one region.

0.8.3 (2020-03-26)
------------------

* **Bug Fix:** Handle all ``account_id`` fields as strings. These were previously incorrectly handled as numeric fields, which prevented working with accounts having IDs that start with zero. The ``account_id`` field in your ``manheim-c7n-tools.yml`` file should be quoted as a string.
* Stop building c7n API docs ourselves, now that upstream API docs are fixed.

0.8.2 (2020-03-20)
------------------

* Bump c7n to release 0.8.46.0
* Bump c7n-mailer release to 0.5.7
* Pin mock package to 3.0.5
* Remove python2

0.8.1 (2019-11-08)
------------------

* Bump c7n to release 0.8.45.2
* Bump c7n-mailer release to 0.5.6

0.8.0 (2019-08-28)
------------------

* Add new config option ``policy_source_paths`` for merging separate policy repos into a single ruleset
* Update ``policygen`` to read from the source paths if the new config option is present

0.7.3 (2019-06-25)
------------------

* Fix ArgumentParser error preventing ``dryrun-diff`` from being run as standalone entrypoint (as opposed to ``manheim-c7n-runner`` step).
* Fix Python3 error in ``dryrun-diff``.

0.7.2 (2019-06-24)
------------------

* Fix error in ``policygen`` script / step when running under Python3.

0.7.1 (2019-06-24)
------------------

* Fix for README not rendering on pypi.org.

0.7.0 (2019-06-24)
------------------

* Code migrated from private project/repository to GitHub.com under Apache2 license; first public release.
