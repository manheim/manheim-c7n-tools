.. _`configuration`:

=============
Configuration
=============

**TODO** document the configuration file format and contents; link to :ref:`policies.repo_layout`.

Ideally also provide an example configuration repository, along with a sample Jenkinsfile.

Configuration File
------------------

By default, ``manheim-c7n-tools`` and related commands (such as ``policygen``) use a configuration file at ``./manheim-c7n-tools.yml``. The schema of this configuration file is documented in the :py:const:`~manheim_c7n_tools.config.MANHEIM_CONFIG_SCHEMA` constant in the source code.
