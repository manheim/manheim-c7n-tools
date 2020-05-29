.. _usage:

Installation and Usage
======================

.. _usage.prerequisites:

Prerequisites
-------------

In order to run ``manheim-c7n-runner`` or the other tools/entrypoints packaged with this project, you will need a directory or git repository containing your configuration files and policies. The content and layout is described under :ref:`configuration`. In order to fill in all of the values in the configuration files, you will need to have created the required infrastructure in your account(s):

* an IAM Role for the c7n Lambdas to run under, with the required policies
* a CloudWatch Log Group for c7n in each region (with identical naming except for the region names)
* an S3 bucket for c7n's output in each region (with identical naming except for the region names)
* an SQS queue for c7n-mailer in at least one region
* optionally, a Dead Letter SQS queue in each region for monitoring failed c7n and mailer Lambda invocations

We manage all of these in each of our accounts via a `terraform <https://www.terraform.io/>`_ module.

.. _usage.installation:

Installation
------------

We highly recommend using the ``manheim/manheim-c7n-tools`` Docker image over a local Python installation, as the Docker image has the necessary versions of all dependencies installed. If you really want to install the Python package directly, instructions for installing for local development can be found in :ref:`development.local`.

.. _usage.usage:

Usage
-----

.. warning::
   If you follow a CI process for your policies like we do, it is **highly** recommended that you run locally using read-only AWS credentials, to prevent any accidental policy executions from potentially un-reviewed changes!

To run one of the included entrypoints via the Docker image, run the following from within your :ref:`configuration repo directory <configuration>`:

.. code-block:: shell

    docker run -it --rm \
      -v $(pwd):/configs \
      --workdir /configs \
      -e "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" \
      -e "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" \
      -e "AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN" \
      manheim/manheim-c7n-tools:latest \
      ENTRYPOINT

Where ``ENTRYPOINT`` is one of the :ref:`entrypoints <index.main_components>` contained in this package and the ``AWS_`` environment variables are your credentials for the AWS account you're running against (or the credentials you use to assume roles, if using ``manheim-c7n-runner`` AssumeRole support).

If you're using custom c7n-mailer templates, you can mount them in to the container at ``/manheim_c7n_tools/manheim_c7n_tools/mailer-templates`` and they will be picked up by the "mailer" step of ``manheim-c7n-runner``. Assuming they're in a ``mailer-templates`` subdirectory of your configuration repo, this can be done by adding ``-v $(pwd)/mailer-templates:/manheim_c7n_tools/manheim_c7n_tools/mailer-templates`` to the ``docker run`` command above.

To run the Python scripts locally without Docker, install as described in :ref:`development.local` and then run the appropriate entrypoint.

.. _usage.mailer-replay:

Using c7n-mailer-replay
-----------------------

Occasionally when running `c7n-mailer <https://github.com/cloud-custodian/cloud-custodian/tree/master/tools/c7n_mailer>`__, you may have template issues that result in c7n-mailer throwing exceptions and leaving messages in the SQS queue. One way to debug these template errors is by using the actual data from SQS to render a template locally via the `c7n-mailer-replay entrypoint <https://github.com/cloud-custodian/cloud-custodian/tree/master/tools/c7n_mailer#testing-templates-and-recipients>`__ and iterate on fixing the template.

Using this entrypoint via manheim-c7n-tools is a bit difficult, as we don't have the separate c7n-mailer configuration file that it requires. Here's the process for using ``c7n-mailer-replay`` from manheim-c7n-tools:

1. Clone the git repository that contains your ``mailer-templates`` directory; we'll be working in that clone so you should have a ``./mailer-templates`` in your current working directory.
2. If it's not already there (because you have a multi-repository layout), copy your ``manheim-c7n-tools.yml`` to your current directory.
3. To generate the required ``c7n-mailer.yml`` configuration file, run the following Python script/code in your current directory:

.. code-block:: python

    #!/usr/bin/env python

    from yaml import load, dump
    try:
        from yaml import CLoader as Loader, CDumper as Dumper
    except ImportError:
        from yaml import Loader, Dumper

    with open('manheim-c7n-tools.yml', 'r') as fh:
        data = load(fh, Loader=Loader)

    if isinstance(data, type([])):
        # multi-account config file; we only use the first account
        data = data[0]

    with open('c7n-mailer.yml', 'w') as fh:
        fh.write(dump(data['mailer_config'], Dumper=Dumper))

4. Get the message body of the SQS message that you want to use for testing. This can be done in the AWS Console by browsing to the SQS Queue, viewing messages in it, clicking the "Details" link for the message in question, and then copying the content of the "Message Body" text area. This will usually be a long base64-encoded string.
5. Save the base64-encoded message body, directly as it exists in the SQS message, to ``./message.txt``.
6. Run the ``c7n-mailer-replay`` entrypoint inside Docker with the desired arguments. i.e., to print the result of the rendered template:

.. code-block:: shell

    docker run -it --rm \
      -v $(pwd):/configs \
      --workdir /configs \
      manheim/manheim-c7n-tools:latest \
      c7n-mailer-replay -c mailer.yml -t mailer-templates/ -T message.txt

7. Iterate on template changes as needed. For speed it may be easier to run the Docker image with ``/bin/bash`` as the command and then run ``c7n-mailer-reply`` repeatedly, so the container will not need to be created and destroyed each time you render the template.
8. Remember not to commit any of the temporary files (``c7n-mailer.yml``, ``message.txt``, and possibly your ``manheim-c7n-tools.yml``) to the git repository; only commit your template changes.
