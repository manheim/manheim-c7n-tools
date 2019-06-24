manheim-c7n-tools
=================

[![ReadTheDocs.org build status](https://readthedocs.org/projects/manheim-c7n-tools/badge/?version=latest)](https://manheim-c7n-tools.readthedocs.io/)

[![TravisCI build badge](https://api.travis-ci.org/manheim/manheim-c7n-tools.png?branch=master)](https://travis-ci.org/manheim/manheim-c7n-tools)

[![Docker Hub Build Status](https://img.shields.io/docker/cloud/build/manheim/manheim-c7n-tools.svg)](https://hub.docker.com/r/manheim/manheim-c7n-tools)

[![PyPI Version badge](https://img.shields.io/pypi/v/manheim-c7n-tools.svg)](https://pypi.org/project/manheim-c7n-tools/)

Manheim's Cloud Custodian (c7n) wrapper package, policy generator, runner, and supporting tools.

This project provides common tooling, distributed as a Docker image, for managing Manheim's cloud-custodian (c7n) tooling, including c7n itself, c7n_mailer, and our custom components. This project/repository is intended to be used (generally via the generated Docker image) alongside a configuration repository of a specific layout, containing configuration for one or more AWS accounts.

* **Full Documentation**: <https://manheim-c7n-tools.readthedocs.io/>
* TravisCI Builds: <https://travis-ci.org/manheim/manheim-c7n-tools>
* Docker image: <https://hub.docker.com/r/manheim/manheim-c7n-tools>

For documentation on the upstream cloud-custodian project, please see <https://cloudcustodian.io/docs/index.html> and the source code at <https://github.com/cloud-custodian/cloud-custodian>.

Introduction and Goals
----------------------

Cloud Custodian (a.k.a. c7n) is a flexible rules engine for reporting on and enforcing policy in AWS. Manheim has migrated from Netflix Janitor Monkey to Cloud Custodian for our tag enforcement, resource cleanup, cost reduction, and other policy needs. This project provides common tooling to allow us to deploy and manage c7n across multiple AWS accounts.

We're currently deploying all Cloud Custodian policies via AWS Lambda. The default is to run policies once per day, but other execution triggers are available including arbitrary timer triggers as well as CloudTrail, AWS Config and CloudWatch Events.

A description of the initial tooling that turned into this project can be found in [this blog post](https://blog.jasonantman.com/2017/10/cloud-custodian-architecture-deployment-and-policy-preprocessing/).

.. _index.main_components:

Main Components
---------------

The following commands are available in the Docker container (or Python installation), generated as Python package entrypoints:

* [manheim-c7n-runner](https://manheim-c7n-tools.readthedocs.io/en/latest/runner/) - A single entrypoint to wrap running one or more, or all, of the following steps (as well as `custodian` itself, `c7n-mailer` deploy, and Sphinx documentation build) in the proper order, in either run (real) or dryrun mode.
* [policygen](https://manheim-c7n-tools.readthedocs.io/en/latest/policygen/) - The python script to generate the actual custodian YML config files from a configuration repo/directory. Must be run from a config repository directory.
* [s3-archiver](https://manheim-c7n-tools.readthedocs.io/en/latest/s3archiver/) - Script to clean up custodian S3 buckets by moving logs from any deleted policies to an "archived-logs/" prefix.
* [dryrun-diff](https://manheim-c7n-tools.readthedocs.io/en/latest/dryrun-diff/) - Script to compare the number of resources matched per-policy, per-region between a dryrun and the last actual run of each policy, and write the results to a Markdown file (to be added as a comment on the PR).
* ``errorscan`` - Script using boto3 to examine CloudWatch Metrics, Logs, and SQS Dead Letter Queue for cloud-custodian Lambda functions, and alert on any failed executions, dead letters, etc.
* c7n's built-in `mugc` Lambda garbage collection. This is vendored-in to manheim-c7n-tools, as c7n provides it only as a non-executable Python source file in their git repo.
* c7n's `c7n-mailer` installed as a dependency for convenience.

Installation and Usage
----------------------

See [Installation and Usage](https://manheim-c7n-tools.readthedocs.io/en/latest/usage/)
