Changelog
=========

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
