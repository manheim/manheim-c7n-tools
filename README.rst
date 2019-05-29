manheim-c7n-tools
=================

Manheim's Cloud Custodian (c7n) wrapper package, policy generator, runner, and supporting tools.

This project provides common tooling, distributed as a Docker image, for managing Manheim's cloud-custodian (c7n) tooling, including c7n itself, c7n_mailer, and our custom components. This project/repository is intended to be used (generally via the generated Docker image) alongside a configuration repository of a specific layout, containing configuration for one or more AWS accounts.

* **Full Documentation**: **TODO**
* TravisCI Builds: **TODO**
* Docker image: **TODO**

For documentation on the upstream cloud-custodian project, please see `https://cloudcustodian.io/docs/index.html <https://cloudcustodian.io/docs/index.html>`_ and the source code at `https://github.com/cloud-custodian/cloud-custodian <https://github.com/cloud-custodian/cloud-custodian>`_.

======================
Introduction and Goals
======================

Cloud Custodian (a.k.a. c7n) is a flexible rules engine for reporting on and enforcing policy in AWS. CAIS Release Engineering is migrating from Netflix Janitor Monkey to Cloud Custodian for our tag enforcement, resource cleanup, cost reduction, and other policy needs. This project provides common tooling to allow us to deploy and manage c7n across multiple AWS accounts.

We're currently deploying all Cloud Custodian policies via AWS Lambda. The default is to run policies once per day, but other execution triggers are available including arbitrary timer triggers as well as CloudTrail, AWS Config and CloudWatch Events.

===============
Main Components
===============

The following commands are available in the Docker container (or Python installation), generated as Python package entrypoints:

* :ref:`manheim-c7n-runner <runner>` - A single entrypoint to wrap running one or more, or all, of the following steps in the proper order, in either run (real) or dryrun mode.
* :ref:`policygen` - The python script to generate the actual custodian YML config files from a configuration repo/directory. Must be run from a config repository directory.
* :ref:`s3-archiver` - Script to clean up custodian S3 buckets by moving logs from any deleted policies to an "archived-logs/" prefix.
* :ref:`dryrun-diff` - Script to compare the number of resources matched per-policy, per-region between a dryrun and the last actual run of each policy, and write the results to a Markdown file (to be added as a comment on the PR).
* :py:mod:`mugc <manheim_c7n_tools.vendor.mugc>` - built-in c7n Lambda garbage collection. The Docker image provides a wrapper for running this more easily, as c7n provides it only as a non-executable Python source file in their git repo.

======================
Installation and Usage
======================

**TODO** - Link to docs pages for either local installation or Docker usage (need a page for Docker specifically). Must mention requirements file for installation.
