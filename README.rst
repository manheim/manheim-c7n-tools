manheim-c7n-tools
=================

.. image:: https://readthedocs.org/projects/manheim-c7n-tools/badge/?version=latest
   :target: https://manheim-c7n-tools.readthedocs.io/
   :alt: ReadTheDocs.org build status

.. image:: https://api.travis-ci.org/manheim/manheim-c7n-tools.png?branch=master
   :target: https://travis-ci.org/manheim/manheim-c7n-tools
   :alt: TravisCI build badge

Manheim's Cloud Custodian (c7n) wrapper package, policy generator, runner, and supporting tools.

This project provides common tooling, distributed as a Docker image, for managing Manheim's cloud-custodian (c7n) tooling, including c7n itself, c7n_mailer, and our custom components. This project/repository is intended to be used (generally via the generated Docker image) alongside a configuration repository of a specific layout, containing configuration for one or more AWS accounts.

* **Full Documentation**: `https://manheim-c7n-tools.readthedocs.io/ <https://manheim-c7n-tools.readthedocs.io/>`__
* TravisCI Builds: https://travis-ci.org/manheim/manheim-c7n-tools
* Docker image: **TBD**

For documentation on the upstream cloud-custodian project, please see `https://cloudcustodian.io/docs/index.html <https://cloudcustodian.io/docs/index.html>`_ and the source code at `https://github.com/cloud-custodian/cloud-custodian <https://github.com/cloud-custodian/cloud-custodian>`_.

======================
Introduction and Goals
======================

Cloud Custodian (a.k.a. c7n) is a flexible rules engine for reporting on and enforcing policy in AWS. Manheim has migrated from Netflix Janitor Monkey to Cloud Custodian for our tag enforcement, resource cleanup, cost reduction, and other policy needs. This project provides common tooling to allow us to deploy and manage c7n across multiple AWS accounts.

We're currently deploying all Cloud Custodian policies via AWS Lambda. The default is to run policies once per day, but other execution triggers are available including arbitrary timer triggers as well as CloudTrail, AWS Config and CloudWatch Events.

===============
Main Components
===============

The following commands are available in the Docker container (or Python installation), generated as Python package entrypoints:

* `manheim-c7n-runner <https://manheim-c7n-tools.readthedocs.io/en/latest/runner/>`__ - A single entrypoint to wrap running one or more, or all, of the following steps in the proper order, in either run (real) or dryrun mode.
* `policygen <https://manheim-c7n-tools.readthedocs.io/en/latest/policygen/>`__ - The python script to generate the actual custodian YML config files from a configuration repo/directory. Must be run from a config repository directory.
* `s3-archiver <https://manheim-c7n-tools.readthedocs.io/en/latest/s3archiver/>`__ - Script to clean up custodian S3 buckets by moving logs from any deleted policies to an "archived-logs/" prefix.
* `dryrun-diff <https://manheim-c7n-tools.readthedocs.io/en/latest/dryrun-diff/>`__ - Script to compare the number of resources matched per-policy, per-region between a dryrun and the last actual run of each policy, and write the results to a Markdown file (to be added as a comment on the PR).
* ``mugc`` - built-in c7n Lambda garbage collection. The Docker image provides a wrapper for running this more easily, as c7n provides it only as a non-executable Python source file in their git repo.

======================
Installation and Usage
======================

**TODO** - Link to docs pages for either local installation or Docker usage (need a page for Docker specifically). Must mention requirements file for installation.
