FROM python:3.7.3-alpine3.9

ARG git_commit
ARG git_url
ARG build_url
ARG version
ARG custodian_version

COPY . /manheim_c7n_tools
RUN cd /manheim_c7n_tools \
  && apk add bash git curl \
  && apk add --no-cache --virtual .build-deps \
      gcc \
      linux-headers \
      make \
      musl-dev \
  && pip install -r requirements.txt \
  && pip install -e . \
  # clean up build dependencies
  && apk del .build-deps \
  && rm -Rf /root/.cache

LABEL com.manheim.commit=$git_commit \
      com.manheim.repo=$git_url \
      com.manheim.build_url=$build_url \
      version=$version
