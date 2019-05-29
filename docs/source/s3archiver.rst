.. _`s3archiver`:

===========
S3 Archiver
===========

Script to clean up custodian S3 buckets by moving logs from any deleted policies to an "archived-logs/" prefix.

The ``s3-archiver`` entry point / command (and :ref:`runner` step) lists all policy names from the current configuration file and then lists all policy output prefixes in the configured S3 bucket. Any policy output prefixes in S3 that do not match a policy name in the current configuration file will be moved to a ``archived-logs/`` prefix for handling via lifecycle rules.

Usage
=====

.. code-block:: none

    $ s3-archiver --help
    usage: s3-archiver [-h] [-v] [-d] REGION_NAME BUCKET_NAME CONF_FILE

    Archive S3 logs for deleted policies

    positional arguments:
    REGION_NAME    AWS region name to run against
    BUCKET_NAME    S3 Bucket Name
    CONF_FILE      path to cloud-custodian config YML file

    optional arguments:
    -h, --help     show this help message and exit
    -v, --verbose  verbose output. specify twice for debug-level output.
    -d, --dry-run  print what would be done; dont move anything
