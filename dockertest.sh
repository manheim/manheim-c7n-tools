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
    >&2 echo "USAGE: dockertest.sh repo/image:tag"
    exit 1
fi

docker run -it --rm "$1" \
  bash -c "policygen -V && s3-archiver -V && dryrun-diff -V && manheim-c7n-runner -V && mugc --help"
