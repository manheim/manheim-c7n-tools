.. _`configuration`:

=============
Configuration
=============

``manheim-c7n-tools`` and :ref:`related commands <index.main_components>` expect to be executed with a current working directory of a "configuration repository", matching the layout described in :ref:`policies.repo_layout`. An example configuration repository can be seen at `https://github.com/manheim/manheim-c7n-tools/tree/master/example_config_repo <https://github.com/manheim/manheim-c7n-tools/tree/master/example_config_repo>`_. An example of a repository utilizing the policygen ability to layer multiple sets of policies can be seen at `https://github.com/manheim/manheim-c7n-tools/tree/master/example_config_multi_repo <https://github.com/manheim/manheim-c7n-tools/tree/master/example_config_multi_repo>`_.

Configuration File
------------------

By default, ``manheim-c7n-tools`` and related commands (such as ``policygen``) use a configuration file at ``./manheim-c7n-tools.yml``. The schema of this configuration file is documented in the :py:const:`~manheim_c7n_tools.config.MANHEIM_CONFIG_SCHEMA` constant in the source code. In addition, a commented example is available `in the GitHub repo <https://github.com/manheim/manheim-c7n-tools/blob/master/example_config_repo/manheim-c7n-tools.yml>`_.
