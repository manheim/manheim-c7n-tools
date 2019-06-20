#!/bin/bash -x
# Copyright 2017-2019 Manheim / Cox Automotive
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -x
set -e

if [ -z "$1" ]; then
    >&2 echo "USAGE: build_or_deploy.sh [build|dockerbuild|push|dockerbuildtest]"
    exit 1
fi

function gettag {
    # if it's a build of a tag, return that right away
    [ ! -z "$TRAVIS_TAG" ] && { echo $TRAVIS_TAG; return 0; }
    # otherwise, prefix with PR number if available
    prefix=''
    [ ! -z "$TRAVIS_PULL_REQUEST" ] && [[ "$TRAVIS_PULL_REQUEST" != "false" ]] && prefix="PR${TRAVIS_PULL_REQUEST}_"
    ref="test_${prefix}$(git rev-parse --short HEAD)_$(date +%s)"
    echo "${ref}"
}

function getversion {
    python -c 'from manheim_c7n_tools.version import VERSION; print(VERSION)'
}

function getbuildurl {
  [ ! -z "$TRAVIS_BUILD_WEB_URL" ] && { echo $TRAVIS_BUILD_WEB_URL; return 0; }
  echo "local"
}

function dockertoxbuild {
    tag=$(gettag)
    version=$(getversion)
    buildurl=$(getbuildurl)
    echo "Building Docker image..."
    docker build \
      --build-arg version="$tag" \
      --build-arg git_commit="$(git rev-parse --short HEAD)" \
      --build-arg build_url="$buildurl" \
      --no-cache \
      -t "manheim/manheim-c7n-tools:${tag}" .
    echo "Built image and tagged as: manheim/manheim-c7n-tools:${tag}"
}

function dockerbuildtest {
    tag=$(gettag)
    dockertoxbuild
    ./dockertest.sh "manheim/manheim-c7n-tools:${tag}"
}

function pythonbuild {
    rm -Rf dist
    python setup.py sdist bdist_wheel
    ls -l dist
}

function pythonpush {
    pip install twine
    twine upload dist/*
}

if [[ "$1" == "build" ]]; then
    pythonbuild
elif [[ "$1" == "dockerbuild" ]]; then
    dockertoxbuild
elif [[ "$1" == "push" ]]; then
    pythonpush
elif [[ "$1" == "dockerbuildtest" ]]; then
    dockerbuildtest
else
    >&2 echo "USAGE: do_docker.sh [build|dockerbuild|push|dockerbuildtest]"
    exit 1
fi
