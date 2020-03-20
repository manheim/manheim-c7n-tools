Changelog
=========

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
