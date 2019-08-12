.. _policygen:

=========
Policygen
=========

For API documentation, see :py:mod:`manheim_c7n_tools.policygen`.

``policygen`` allows us to maintain our policies in git as one ``.yml`` file per policy, in directories of global, account-specific, or region-specific policies. ``policygen`` reads all of them, selects the policies for the current account, interpolates our defaults, performs some sanity/safety checks on them, and then writes per-region ``custodian_REGION.yml`` containing all of the policies for each region. In the final ``custodian_REGION.yml`` files, some :ref:`Interpolation <policies.region_interpolation>` is performed.

Policygen expects the repository it's run from to have a ``policies/`` directory that matches the :ref:`policies.repo_layout`.

Policy Safety Tests
===================

``policygen`` runs some checks against policies to ensure that they seem safe and sane. To add to these, see the docs on the :py:meth:`manheim_c7n_tools.policygen.PolicyGen._check_policies` method.

.. _`policygen.defaults_merging`:

Defaults merging
================

Each policy is augmented with defaults from ``defaults.yml``. The simple overview of the merging procedure is:

-  We start with ``defaults.yml``
   as a base, and layer the policy-specific config on top of it.
-  We merge recursively (i.e. deep merging).
-  Keys from the policy overwrite identical keys in the defaults; the policy-specific config always wins over the defaults.
-  In the case of arrays (i.e. the ``actions`` list), the end result includes all elements that are simple data types (i.e. strings). For
   dictionary items in arrays, we look at the value of the ``type`` element; if both the policy and the defaults arrays have dictionaries
   with the same ``type``, we merge them together, with the policy overwriting the defaults. Defaults dictionaries without a matching
   ``type`` in the policy will always be in the final result, **except for** ``actions`` with a type of ``notify``; policies that do not
   have a ``type: notify`` will not have one added. This allows us to set defaults for dictionaries embedded in arrays, like the "type:
   notify" action.
-  **Note** there is some special handling for the "mode" key: If the mode has a "type" of anything other than "periodic", it will not
   be changed at all except by having "tags" updated iff it already has a "tags" key (even if that key has an empty value). As such,
   modes other than "periodic" must have their full configuration (except tags, which must be present but can be empty) specified in
   every policy.
-  After all that, if the ``always_notify`` configuration option is set, ensure that a ``type: notify`` action exists on the policy
   with the specified transport and at least the specified set of ``to`` destinations, adding one if not already present.

Details
-------

Defaults are merged in to the policies by ``policygen.py``. Merging is
performed between dictionaries (hashes; mapping types) recursively,
starting with the top-level (i.e. the whole file):

-  We begin with a copy of the defaults and then iterate over all of the
   items in the policy-specific configuration as key/value pairs,
   updating the defaults as we go to build the final policy:
-  If the key in the policy is a top-level key called "mode" and its "type"
   sub-key has a value other than "periodic", it short-circuits the defaults
   merging process and has nothing changed other than updating the "tags" key
   if it is already present.
-  If the key from the policy-specific config isn't in the defaults, we
   add the key and value and move on. Otherwise;
-  If the value is an array, we use special array merging logic (see
   below) and update with the result of the array merge.
-  If the value is another dictionary, we call the same function
   recursively and update with its result.
-  If the value isn't an array or dictionary, we assume it to be a
   simple type (string, int, etc.) and overwrite the default value with
   the one specified in the policy-specific configuration.
-  The end result of this is returned.

Array merging is somewhat special, to let us set defaults for actions:

-  We begin with the policy itself as the base array, instead of the
   defaults.
-  Any non-dictionary items in defaults that aren't in the policy are
   appended to the policy array.
-  Any dictionary items in the policy array with a "type" key/value pair
   that matches one of the dictionary items in the defaults array, will
   have additional key/value pairs added from the defaults dictionary.
-  Any defaults dictionaries not handled under the previous condition
   will be appended to the result, with the exception of a
   ``type: notify`` dictionary in the ``['actions']`` path.

Mutiple Repository Layout
=========================

In order to facilitate separation of organizational rules from team or account specific rules, the policies directory can contain subdirectories to be merged into a single ruleset. Directories will be merged using the same logic described in the defaults merging documentation. An example of a multi-repository layout is at :ref:`policies.repo_layout`

Config changes for Multiple Repositories
----------------------------------------

To use multiple subdirectories, the configuration file must be updated with a list of directories that should be considered. Order matters, as preference will be given to repositories lower in the list in the case of conflicting configurations. A new ``policy_source_paths`` configuration option has been added, and should contain a list of subdirectories to consider in the order of least to most specific.

.. code-block:: yaml
    policy_source_paths:
      - shared
      - team
      - app

Defaults with Multiple Repositories
-----------------------------------

There can be only one ``defaults.yaml`` file in use. The tool will search all configured repository paths for a ``defaults.yaml`` file at the root of each path in the order specified in the ``policy_source_paths`` option. The last file found will be used. If no ``defaults.yaml`` file is found in the repository paths, it will look in the ``policies`` directory itself. At least one ``defaults.yaml`` must be present.

Overriding rules
----------------

Overriding rules is based on naming. **Rules will not be merged, only replaced.** If a rule appears in a lower repository it will replace a rule with the same name in a higher repository.