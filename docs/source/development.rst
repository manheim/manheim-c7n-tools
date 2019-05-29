===========
Development
===========

* Open a pull request for changes. TravisCI will test them.
* To cut a release, bump the version number in ``manheim_c7n_tools/version.py``, update ``CHANGES.rst``, and open a pull request for that. When merged to master, TravisCI will trigger the release.

Local Development and Testing
=============================

1. Clone this repo locally.
2. ``virtualenv --python=python3.7 .``
3. ``source bin/activate``
4. ``pip install 'tox>=3.4.0'``

To run tests: ``tox``

For information on how to run the actual commands locally, see :ref:`index`.
