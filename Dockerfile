FROM python:3.7.3-alpine3.9

ARG git_commit
ARG git_url
ARG build_url
ARG version
ARG custodian_version

COPY . /manheim_c7n_tools
RUN cd /tmp \
  # install bash
  && apk add bash git curl \
  # need gcc and friends to compile some dependencies
  && apk add --no-cache --virtual .build-deps \
      gcc \
      linux-headers \
      make \
      musl-dev \
  # BEGIN c7n installation. c7n-mailer and mugc are only in the git repo not
  # the PyPI package(s), so we might as well just install it all from source
  # TODO: switch to an official release once > 0.8.43.1 is out
  && curl -L -o c7n.tar.gz https://github.com/cloud-custodian/cloud-custodian/archive/${custodian_version}.tar.gz \
  && mkdir /c7n \
  && tar -xzvf c7n.tar.gz -C /c7n --strip 1 \
  && rm -f /tmp/c7n.tar.gz \
  && cd /c7n \
  && pip install . \

  && cd /c7n/tools/c7n_mailer \
  && pip install -r requirements.txt \
  && python setup.py develop \
  # END c7n installation
  && cd /manheim_c7n_tools \
  && pip install -e . \
  # clean up build dependencies
  && apk del .build-deps \
  && rm -Rf /root/.cache

LABEL com.manheim.commit=$git_commit com.manheim.repo=$git_url com.manheim.build_url=$build_url version=$version
