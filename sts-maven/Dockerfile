# syntax=docker/dockerfile:1.4
FROM azul/zulu-openjdk:8-latest

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get -qq update \
    && apt-get -qqy install curl python3 git \
    && rm -rf /var/lib/apt/lists/*

ARG MAVEN_VERSION=3.8.7
ARG USER_HOME_DIR=/root
ARG BASE_URL=https://apache.osuosl.org/maven/maven-3/${MAVEN_VERSION}/binaries

RUN mkdir -p /usr/share/maven/ref \
    && curl -fsSL -o /tmp/maven.tar.gz ${BASE_URL}/apache-maven-${MAVEN_VERSION}-bin.tar.gz \
    && tar -xzf /tmp/maven.tar.gz -C /usr/share/maven --strip-components=1 \
    && rm -f /tmp/maven.tar.gz \
    && ln -s /usr/share/maven/bin/mvn /usr/bin/mvn

ENV MAVEN_HOME /usr/share/maven
ENV MAVEN_CONFIG "${USER_HOME_DIR}/.m2"
ENV GH_MAVEN_REPO "https://maven.pkg.github.com/bindernews/sts-maven"
ENV GH_USERNAME "your-username"
ENV GH_TOKEN "your-token"

COPY settings-docker.xml /usr/share/maven/ref/
COPY sts-maven.py /opt/
RUN echo "#!/bin/sh\npython3 /opt/sts-maven.py \$*" >/usr/bin/sts-maven \
    && chmod ug+x /usr/bin/sts-maven

WORKDIR "${USER_HOME_DIR}"
CMD [ "/bin/bash" ]
