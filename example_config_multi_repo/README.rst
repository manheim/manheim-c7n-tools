manheim-c7n-tools Example Configuration Repo
============================================

This is an example configuration repository for the `manheim-c7n-tools
<https://github.com/manheim/manheim-c7n-tools>`_ project. Along with the
dependencies (IAM Role, S3 Bucket, and CloudWatch Log Group), this repository
contains an example of all of the configuration required to run
``manheim-c7n-tools`` for an AWS account.

This repository shows an example of a multi-repo configuration. `policies`
directory contains several subdirectories - these can be git submodules or
other means of aggregating several separate rules repositories. Each of these
will be merged together according to the order specified in the
`policy_source_paths` configuration value, with lower repos taking precedence
over higher repos. In order to override a rule, make a copy of the rule from
another repo and change it to match your needs. Rules are overridden based on
rule name, but rule configurations themselves are NOT merged, they are
replaced in their entirety.
