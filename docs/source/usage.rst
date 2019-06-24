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
