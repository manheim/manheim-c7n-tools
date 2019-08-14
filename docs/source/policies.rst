.. _`policies`:

===============
Policy Language
===============

.. _`policies.ours`:

The ``policies/`` directory in the configuration repository contains the c7n policies, one per file. Policies should have a name that matches their filename (``NAME.yml``) and should all have a "comment" or "comments" section that provides a human-readable summary of what the policy does (this comment is used to generate the Current Policies documentation).

All policies are built on top of ``defaults.yml``; see :ref:`policygen.defaults_merging` for further information.

Policies are built via the ``policygen`` command (or the ``manheim-c7n-tools`` policygen step), which runs :ref:`policygen` and generates per-region ``custodian_REGION.yml`` files.

.. _`policies.repo_layout`:

Policy Repository Layout
========================

The overall layout of the configuration repository must be as follows:

::

    manheim-c7n-tools.yml
    policies/
    ├── all_accounts
    │   └── common
    │       └── policy-one.yml
    ├── defaults.yml
    └── ACCOUNT-NAME
        ├── common
        │   ├── policy-three.yml
        │   └── policy-two.yml
        ├── us-east-1
        │   ├── policy-five-us-east-1.yml
        │   └── policy-four-us-east-1.yml
        ├── us-east-2
        │   └── policy-four-us-east-2.yml
        ├── us-west-1
        │   └── policy-four-us-west-1.yml
        └── us-west-2
            └── policy-four-us-west-2.yml

The ``policies/`` directory contains:

* ``defaults.yml``, the defaults used for ALL policies in all accounts (see :ref:`policygen.defaults_merging` for further information).
* A ``all_accounts/`` directory of policies shared identically across all accounts.
* A directory of account-specific policies for each account; the directory name must match the ``account_name`` value in ``manheim-c7n-tools.yml``.

Within each subdirectory (``all_accounts`` or an account name) is a directory called ``common`` and optionally directories for one or more specific regions. Policies in the ``common/`` directory will be applied in all regions and policies in a region-specific directory will only be applied in that region.

When building the final configuration, policies from the account-specific directory will be layered on top of policies from the ``all_accounts/`` directory. A policy with the exact same file and policy name in a per-account directory will override a policy with the same name from the ``all_accounts/`` directory. Similarly, *within the all_accounts/ or account-named directories*, a region-specific policy will override a ``common/`` policy with the same name and filename.

An example configuration repository can be seen at `https://github.com/manheim/manheim-c7n-tools/tree/master/example_config_repo <https://github.com/manheim/manheim-c7n-tools/tree/master/example_config_repo>`_.

.. _`policies.repo_layout_multi`:

Multiple Repository Layout
--------------------------

::

    manheim-c7n-tools.yml
    policies/
    ├── app
    │   ├── defaults.yml
    │   └── ACCOUNT-NAME
    │       ├── us-east-1
    │       │   ├── policy-five-us-east-1.yml
    │       │   └── policy-six-us-east-1.yml
    │       ├── us-east-2
    │       │   └── policy-six-us-east-2.yml
    │       ├── us-west-1
    │       │   └── policy-six-us-west-1.yml
    │       └── us-west-2
    │           └── policy-six-us-west-2.yml
    ├── common
    │   ├── all_accounts
    │   │   └── common
    │   │       └── policy-one.yml
    │   ├── defaults.yml
    │   └── ACCOUNT-NAME
    │       └── common
    │           ├── policy-three.yml
    │           └── policy-two.yml
    └── team
        ├── all_accounts
        │   └── common
        │       └── policy-six.yml
        └── ACCOUNT-NAME
            ├── us-east-1
            │   ├── policy-five-us-east-1.yml
            │   └── policy-four-us-east-1.yml
            ├── us-east-2
            │   └── policy-four-us-east-2.yml
            ├── us-west-1
            │   └── policy-four-us-west-1.yml
            └── us-west-2
                └── policy-four-us-west-2.yml

.. An example configuration for a multiple repository setup can be seen at `https://github.com/manheim/manheim-c7n-tools/tree/master/example_config_multi_repo <https://github.com/manheim/manheim-c7n-tools/tree/master/example_config_multi_repo>`_.

.. _`policies.region_interpolation`:

Policy Interpolation
====================

When :ref:`policygen` generates configuration files for each AWS Region that we deploy into, it will replace all instances of the string ``%%AWS_REGION%%`` with the specific region name. As such, the ``%%AWS_REGION%%`` macro must be used in all policies as well as the mailer config, where the current region needs to be referenced.

The list of regions that we generate configs for is taken from the ``regions`` key of ``manheim-c7n-tools.yml``.

There are also some other values from ``manheim-c7n-tools.yml`` (the :py:class:`~.ManheimConfig` class) that can be interpolated in the policies:

+----------------------+-------------------------+--------------------------------------------------------------------+
| String               | Config Value            | Description                                                        |
+======================+=========================+====================================================================+
| %%AWS_REGION%%       | *n/a*                   | Replaced with the current region name, for each per-region config  |
+----------------------+-------------------------+--------------------------------------------------------------------+
| %%BUCKET_NAME%%      | output_s3_bucket_name   | Name of the S3 bucket used for cloud-custodian output              |
+----------------------+-------------------------+--------------------------------------------------------------------+
| %%LOG_GROUP%%        | custodian_log_group     | Name of the CloudWatch Log Group for custodian to log to           |
+----------------------+-------------------------+--------------------------------------------------------------------+
| %%DLQ_ARN%%          | dead_letter_queue_arn   | ARN of the Dead Letter Queue for Custodian Lambdas                 |
+----------------------+-------------------------+--------------------------------------------------------------------+
| %%ROLE_ARN%%         | role_arn                | ARN of the IAM Role to run Custodian functions with                |
+----------------------+-------------------------+--------------------------------------------------------------------+
| %%MAILER_QUEUE_URL%% | mailer_config.queue_url | c7n-mailer SQS queue URL                                           |
+----------------------+-------------------------+--------------------------------------------------------------------+
| %%ACCOUNT_NAME%%     | account_name            | Configured name of the current AWS account                         |
+----------------------+-------------------------+--------------------------------------------------------------------+
| %%ACCOUNT_ID%%       | account_id              | Configured ID of the current AWS account                           |
+----------------------+-------------------------+--------------------------------------------------------------------+

In addition, any ``POLICYGEN_ENV_``-prefixed environment variables present when ``policygen`` is run will be interpolated into the configuration. Running policygen with a ``POLICYGEN_ENV_foo`` environment variable set to ``bar`` will result in all occurrences of ``%%POLICYGEN_ENV_foo%%`` in the configuration replaced with ``bar``.

.. _`policies.anatomy`:

Anatomy of a Policy
===================

Policies in this repository are augmented with the contents of ``defaults.yml`` according to the rules described under :ref:`policygen.defaults_merging`.

As an example, our ``onhour-start-ec2`` policy contains:

.. code:: yaml

    # REMINDER: defaults.yml will be merged in to this. See the README.
    name: onhour-start-ec2
    comments: Start tagged EC2 Instances daily at 06:00 Eastern, or per tag value
    resource: ec2
    filters:
      - type: onhour
        onhour: 6
        default_tz: America/New_York
        tag: custodian_downtime
    actions:
      - start
      - type: notify
        violation_desc: The following EC2 Instance(s)
        action_desc: have been started per onhour configuration
        subject: '[cloud-custodian {{ account }}] Onhour Started EC2 Instances in {{ region }}'
    mode:
      schedule: rate(1 hour)

And our ``defaults.yml`` contains:

.. code:: yaml

    actions:
      - type: notify
        questions_email: foo@example.com
        questions_slack: our-channel
        template: redefault.html
        to:
          - resource-owner
          - 'splunkhec://%%POLICYGEN_ENV_SPLUNK_INDEX%%'
        owner_absent_contact:
          - bar@example.com
          - baz@example.com
        transport:
          queue: 'https://sqs.us-east-1.amazonaws.com/111111111111/cloud-custodian-111111111111'
          type: sqs
    mode:
      execution-options: {log_group: /cloud-custodian/111111111111/us-east-1, output_dir: 's3://c7n-logs-111111111111/logs'}
      role: arn:aws:iam::111111111111:role/cloud-custodian-111111111111
      schedule: rate(1 hour)
      tags: {Component: onhour-start-ec2, Environment: dev, OwnerEmail: foo@example.com,
        Project: cloud-custodian}
      timeout: 300
      type: periodic

After merging with ``defaults.yml``, the policy for the us-east-1 region of a sample "dev" account becomes (this example has been manually sorted to look more like the original, above; the actual output will have keys sorted alphabetically):

.. code:: yaml

    name: onhour-start-ec2
    comments: Start tagged EC2 Instances daily at 06:00 Eastern, or per tag value
    resource: ec2
    filters:
      - type: onhour
        onhour: 6
        default_tz: America/New_York
        tag: custodian_downtime
    actions:
      - start
      - type: notify
        violation_desc: The following EC2 Instance(s)
        action_desc: have been started per onhour configuration
        subject: '[cloud-custodian {{ account }}] Onhour Started EC2 Instances in {{ region }}'
        questions_email: foo@example.com
        questions_slack: our-channel
        template: redefault.html
        to:
          - resource-owner
          - 'splunkhec://%%POLICYGEN_ENV_SPLUNK_INDEX%%'
        owner_absent_contact:
          - bar@example.com
          - baz@example.com
        transport:
          queue: 'https://sqs.us-east-1.amazonaws.com/111111111111/cloud-custodian-111111111111'
          type: sqs
    mode:
      execution-options: {log_group: /cloud-custodian/111111111111/us-east-1, output_dir: 's3://c7n-logs-111111111111/logs'}
      role: arn:aws:iam::111111111111:role/cloud-custodian-111111111111
      schedule: rate(1 hour)
      tags: {Component: onhour-start-ec2, Environment: dev, OwnerEmail: foo@example.com,
        Project: cloud-custodian}
      timeout: 300
      type: periodic

The full list of top-level keys valid for a policy can be found by viewing the source code of :py:func:`c7n.schema.generate <cloud custodian:c7n.schema.generate>` or via the ``custodian`` CLI ``schema`` command, but the above example illustrates the keys that most, if not all, of our policies will have.

-  **name** - The unique name of the policy. For this repo, the filename must be the policy name with a ``.yml`` suffix.
-  **comments** - A one- or two-sentence description of what the policy does. The Jenkins deployment job extracts all of these
   and uses them to build the generated documentation for the configuration repo.
-  **resource** - The AWS resource type that this policy acts on; e.g. ``ec2``, ``asg``, ``rds``, etc. Supported resource
   types can be found in the upstream documentation; see the
   :py:mod:`"type" attributes (strings) of the various c7n.resources classes <cloud custodian:c7n.resources>`.
-  **filters** - Filters tell a policy which resources it should match. The ``filters`` key here is an array/list
   of 0 or more filters to select resources that the policy should match. Multiple filters are ``and``-ed together,
   unless you nest them under an ``or`` block (see the upstream documentation on :std:doc:`collection operators <cloud custodian:filters>`).
   See the :ref:`Filters <policies.filters>` section, below, for more information.
-  **actions** - Actions tell c7n what to do with or about resources that the filters matched. The
   ``actions`` key here is an array/list of 0 or more actions for this policy to take. See the
   :ref:`Actions <policies.actions>` section, below, for more information.
-  **mode** - The ``mode`` key determines how the policy will be deployed and run. See the
   :ref:`Mode <policies.mode>` section, below, for more information.

.. _`policies.filters`:

Filters
-------

Cloud-custodian has support for many different kinds of filters to match various resource attributes.
Upstream documentation exists on both the :ref:`Generic filters <cloud custodian:filters>`
as well as the :ref:`resource-specific filters <cloud custodian:policy>`.
In addition to that manually-curated documentation, there is also generated
documentation for the :py:mod:`generic <cloud custodian:c7n.filters>`
and :py:mod:`resource-specific filters <cloud custodian:c7n.resources>`, as well as the source
code for each (which is liked from that documentation).

-  The :ref:`Generic value filters <cloud custodian:filters>` can match any attribute of the
   resource instance, which is generally the return value of the Describe AWS API call for the
   resource type. There are also some transformations that can be performed on the values, such
   as type conversion, array counting, normalization (lower-case) or calculating age from a date type.
-  :py:mod:`VPC filters <cloud custodian:c7n.filters.vpc>` for things like subnet, security groups, etc.
-  :py:mod:`IAM filters <cloud custodian:c7n.filters.iamaccess>` to assist with finding cross-account or public access in policies.
-  :py:mod:`Health filters <cloud custodian:c7n.filters.health>` to identify resources with associated
   `AWS Health <https://aws.amazon.com/documentation/health/>`_ events.
-  :py:mod:`Metric filters <cloud custodian:c7n.filters.metrics>` to retrieve and filter based on CloudWatch metrics for resources.
-  The :py:mod:`offhours filters <cloud custodian:c7n.filters.offhours>`.

.. _`policies.actions`:

Actions
-------

Cloud-custodian has both generic/global actions (such as ``notify``) and resource-specific actions
(such as ``stop`` and ``start``). Some actions are specified as only a string (i.e. ``stop`` or
``start``), whereas others need to be specified as a dictionary/hash/mapping including configuration options.

:py:mod:`Global actions <cloud custodian:c7n.actions>` include:

-  :py:class:`Notify <cloud custodian:c7n.actions.notify.Notify>` - Send email to static
   addresses, or addresses from tags on the resource, via
   `c7n\_mailer <https://github.com/capitalone/cloud-custodian/tree/master/tools/c7n_mailer>`_.
   Our defaults include configuration required for using this action with our c7n\_mailer instance.
   The only configuration needed to make this action work is as shown in the example above; specifically,
   the ``type: notify`` key and the ``subject``, ``violation_desc`` and ``action_desc`` keys.
-  :py:class:`invoke-lambda <cloud custodian:c7n.actions.invoke.LambdaInvoke>` - Invoke an arbitraty Lambda
   function, passing it details of the policy, action, triggering event, and matched resource(s).
-  :py:class:`modify-security-groups <cloud custodian:c7n.actions.network.ModifyVpcSecurityGroupsAction>`- Modify the security groups assigned to a resource.
-  :py:class:`put-metric <cloud custodian:c7n.actions.metric.PutMetric>` - Send a custom metric to CloudWatch

To identify available resource-specific actions, either find the appropriate resource type module in the
:py:mod:`resource-specific actions <cloud custodian:c7n.resources>` or the
`c7n source code <https://github.com/capitalone/cloud-custodian/tree/master/c7n/resources>`_
and find all classes in it that are based on ``c7n.actions.Action``, or use the ``custodian schema``
command line tool. There is also
:ref:`manually-curated documentation on resource-specific filters and actions <cloud custodian:policy>`
that is helpful but incomplete.

In addition to ``notify``, some of our most-used actions are the various resource-specific ``stop`` or
``suspend`` and ``start`` or ``resume`` actions, as well as the ``terminate`` or ``delete`` actions,
as well as the resource-specific actions to add/modify/delete tags and tag ("mark") a resource for later action.

.. _`policies.mark_for_op`:

Marking Resources for Later Action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**IMPORTANT:** See the :ref:`Data Collection/Notification to Action Transition <policies.action_transition>` section, below.

c7n has built-in logic for using tags to "mark" resources for action at a future time. Note that these actions are
actually resource-specific, and unfortunately some of them have different names on different resources.

The following snippet will mark matched resources with a ``c7n-foo`` tag, with a value of the specified message.
In the message, ``{op}`` will be replaced with the operation (``delete``) and ``{action_date}`` will be replaced
with the date when the action should occur (in this example, the current time plus 5 days).

.. code:: yaml

    filters:
      # not tagged for this policy; otherwise, we'd just keep pushing the mark date forward
      - {'tag:c7n-foo': absent}
    actions:
      - type: mark-for-op
        tag: c7n-foo
        op: delete
        message: "asg-inactive-mark: {op}@{action_date}"
        days: 5

In a separate policy, we can then filter for resources which were marked for a specific action
at or before the current date/time with the ``marked-for-op`` filter:

.. code:: yaml

    filters:
      - type: marked-for-op
        tag: c7n-asg-inactive
        op: delete

That example will filter all resources that were marked for deletion at
or before the current time, with the ``c7n-asg-inactive`` tag.

The ``skew`` parameter on the marked filter skews the current date by adding a number of days to it.
This allows us to filter for resources that are marked for an operation N days in the future, i.e.
to send out a warning notification ahead of time. The following filter will match the same
resources as the previous example, but two days before that example.

.. code:: yaml

    filters:
      - type: marked-for-op
        tag: c7n-asg-inactive
        op: delete
        skew: 2

.. _`policies.mark_unmark_skew`:

The combination of these actions and filters are commonly used to build a "group" of four complementary policies:

#. A ``-mark`` policy matches desired resources with a filter and uses the ``mark-for-op`` action to tag them for action at a later date. Note that
   it is **extremely important** to make sure the policy also incldes a filter to exclude resources that already have the marking tag present;
   if not, the date to take action will continually move forward every time the policy runs, and the action will never be taken.
#. An ``-unmark`` policy matches resources that have the ``mark`` tag present but no longer meet the desired criteria, and removes the mark
   tag from them. For example: if we're writing a policy to identify and terminate EC2 instances lacking required tags, the ``-unmark`` policy
   would match resources that were previously marked by its counterpart (1) but now *have* the required tags, and would remove the marking
   tag from them.
#. An early-action policy using ``skew`` that warns owners of impending action, and may take some preliminary action (i.e. stopping an EC2
   instance a few days before it will be terminated).
#. A termination/deletion policy that takes the final action.

.. _`policies.mode`:

Mode
----

We have standardized on deploying our policies as Lambda functions, to take advantage of c7n's excellent
:std:doc:`cloud custodian:aws/policy/lambda`. The ``type`` key of the ``mode`` section
of the policy defines how the policy will be deployed and executed.
``defaults.yml`` should specify everything needed to deploy a policy in ``periodic`` mode. If the ``mode`` section is completely
omitted from a policy, the default periodic mode will be applied.

Supported ``mode`` ``type`` options for Lambda functions include:

-  `periodic <https://cloudcustodian.io/docs/policy/lambda.html#periodic-function>`_ - (**default for our policies**)
   runs on a set schedule using timer-based CloudWatch Events as a trigger.
-  `cloudtrail <https://cloudcustodian.io/docs/policy/lambda.html#cloudtrail-api-calls>`_ - runs every time a
   CloudTrail event of a certain type is received. Note that tags may not have been applied to resources yet when this triggers.
-  `ec2-instance-state <https://cloudcustodian.io/docs/policy/lambda.html#ec2-instance-state-events>`_ - runs every
   time an EC2 Instance enters the specified state (e.g. ``running``, ``stopped``, ``pending``, etc). Note that tags may not
   have been applied to instances yet when this triggers.
-  `config-rule <https://cloudcustodian.io/docs/policy/lambda.html#config-rules>`_ - triggers via AWS Config rules.
   Note that not all resource types are supported by AWS Config; see the
   `AWS Config - Supported Resources <https://docs.aws.amazon.com/config/latest/developerguide/resource-config-reference.html>`_
   documentation for a list of which resource types are supported.

For full documentation on the required and optional configuration keys for each mode, see the upstream documentation.

Other keys under the ``mode`` section include:

-  **role** - the IAM role that the policy executes under. They should all use the same terraform-managed role.
-  **tags** - Tags to apply to the Lambda function. ``policygen.py`` will add the policy name as the ``Component`` tag.
-  **timeout** - The timeout, in seconds, for the Lambda function. This should be left at the default (maximum) of 300.
-  **execution\_options** - Internal options of the Lambda function. Our defaults send logs to a CloudWatch log group
   and output to an S3 bucket, and setup the Dead Letter Queue.

.. _`policies.action_transition`:

Data Collection/Notification to Action Transition
=================================================

A common pattern that we use when testing new policies is to set up some
policies to either only send email notifications or to only collect data,
analyze that data, and then enable real actions (i.e. stop,
terminate, delete, etc.) after some data has been collected. However it
is **very important** to note that if a "testing only" policy used the
``mark-for-op`` action to tag a resource for later action, and actions
are later enabled for corresponding policies, the actions might be taken
immediately when enabled as a result of the "notify only" policies
marking resources for action.

As a result, when adding actions to policies that have been running in
data collection mode, it's important to manually purge the relevant tags
so the policies don't take any action based on tags applied during data
collection.

For example, if you're adding a "delete" action to policies that were
previously only collecting data and included a mark action like:

.. code:: yaml

    - type: mark-for-op
      tag: c7n-foo-policy
      op: delete
      message: "foo-mark {op}@{action_date}"
      days: 7

Before enabling the real delete action, you should purge all of those
tags with something like (example for EC2 instances):

.. code:: bash

    TAGNAME=c7n-foo-policy
    for i in $(aws ec2 describe-instances --filters Name=tag-key,Values=$tagname --output text --query 'Reservations[*].Instances[*].[InstanceId]')
    do
      echo "removing tag from: $i"
      aws ec2 delete-tags --resources $i --tags Key=$tagname
    done
