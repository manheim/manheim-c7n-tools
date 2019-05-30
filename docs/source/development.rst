===========
Development
===========

* Open a pull request for changes. TravisCI will test them.
* To cut a release, bump the version number in ``manheim_c7n_tools/version.py``, update ``CHANGES.rst``, and open a pull request for that. Once merged to master, tag the release in GitHub and TravisCI will build and deploy the package and Docker image.

Local Development and Testing
=============================

Clone this repo locally on a machine with Python 3.7. Then:

.. code-block:: shell

    virtualenv --python=python3.7 .
    source bin/activate
    pip install 'tox>=3.4.0'
    pip install -r requirements.txt
    python setup.py develop

To run tests: ``tox``

For information on how to run the actual commands locally, see :ref:`index`.
