#!/bin/sh -ex
# In order to use custom templates with c7n-mailer, it needs to be installed
# from source instead of the PyPI package.
# In the Docker image (how this project will actually be used) we do that
# in the Dockerfile. But there's no easy way to install a non-PyPI dependency
# in the `tox` test environment. That's what this script does.
#
# USAGE: ./tox_install_mailer.sh {toxinidir}

TOXINIDIR=$(readlink -f $1)
CUSTODIAN_VER=$(cat ${TOXINIDIR}/custodian_version.txt)

mkdir -p ${TOXINIDIR}/mailer-tox-install/c7n
cd ${TOXINIDIR}/mailer-tox-install
# TODO: switch to an official release once > 0.8.43.1 is out
curl -L -o mailer.tar.gz https://github.com/cloud-custodian/cloud-custodian/archive/${CUSTODIAN_VER}.tar.gz
tar -xzf mailer.tar.gz -C c7n --strip 1
cd ${TOXINIDIR}/mailer-tox-install/c7n

pip install -r requirements.txt
python setup.py install
cd ${TOXINIDIR}/mailer-tox-install/c7n/tools/c7n_mailer
pip install -r requirements.txt
python setup.py install

# cleanup things that might cause problems with docs...
cd ${TOXINIDIR}/mailer-tox-install/c7n
rm -Rf tests c7n/testing.py setup.py
