FROM kathara/base:latest

# syntax=docker/dockerfile:1
# This dockerfile builds the zap stable release
FROM --platform=linux/amd64 debian:bookworm-slim AS builder

RUN apt-get update && apt-get install -q -y --fix-missing \
	wget \
	curl \
	openjdk-17-jdk \
	xmlstarlet \
	unzip && \
	rm -rf /var/lib/apt/lists/*

WORKDIR /zap

# Download and expand the latest stable release
RUN wget -qO- https://raw.githubusercontent.com/zaproxy/zap-admin/master/ZapVersions.xml | xmlstarlet sel -t -v //url |grep -i Linux | wget --content-disposition -i - -O - | tar zxv && \
	mv ZAP*/* . && \
	rm -R ZAP*

# Update add-ons
RUN ./zap.sh -cmd -silent -addonupdate
# Copy them to installation directory
RUN cp /root/.ZAP/plugin/*.zap plugin/ || :

# Setup Webswing
ENV WEBSWING_VERSION=24.2.2
RUN --mount=type=secret,id=webswing_url \
	if [ -s /run/secrets/webswing_url ] ; \
	then curl -s -L  "$(cat /run/secrets/webswing_url)-${WEBSWING_VERSION}-distribution.zip" > webswing.zip; \
	else curl -s -L  "https://dev.webswing.org/files/public/webswing-examples-eval-${WEBSWING_VERSION}-distribution.zip" > webswing.zip; fi && \
	unzip webswing.zip && \
	rm webswing.zip && \
	mv webswing-* webswing && \
	# Remove Webswing bundled examples
	rm -Rf webswing/apps/

FROM debian:bookworm-slim AS final
LABEL maintainer="psiinon@gmail.com"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -q -y --fix-missing \
	make \
	automake \
	autoconf \
	gcc g++ \
	openjdk-17-jdk \
	wget \
	curl \
	xmlstarlet \
	unzip \
	jq \
	git \
	openbox \
	xterm \
	net-tools \
	python3-pip \
	python-is-python3 \
	firefox-esr \
	xvfb \
	x11vnc && \
	rm -rf /var/lib/apt/lists/*

RUN pip3 install \
	--break-system-packages \
	--no-cache-dir \
	--upgrade \
	awscli \
	pip \
	zaproxy \
	pyyaml \
	urllib3

RUN useradd -u 1000 -d /home/zap -m -s /bin/bash zap
RUN echo zap:zap | chpasswd
RUN mkdir /zap && chown zap:zap /zap

WORKDIR /zap

#Change to the zap user so things get done as the right person (apart from copy)
USER zap

RUN mkdir /home/zap/.vnc

# Copy stable release
COPY --link --from=builder --chown=1000:1000 /zap .

COPY --link --from=builder --chown=1000:1000 /zap/webswing /zap/webswing

ARG TARGETARCH
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-$TARGETARCH
ENV PATH=$JAVA_HOME/bin:/zap/:$PATH
ENV ZAP_PATH=/zap/zap.sh

# Default port for use with health check
ENV ZAP_PORT=8080
ENV IS_CONTAINERIZED=true
ENV HOME=/home/zap/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

COPY --link --chown=1000:1000 zap* CHANGELOG.md /zap/
COPY --link --chown=1000:1000 webswing.config /zap/webswing/
COPY --link --chown=1000:1000 webswing.properties /zap/webswing/
COPY --link --chown=1000:1000 policies /home/zap/.ZAP/policies/
COPY --link --chown=1000:1000 policies /root/.ZAP/policies/
# The scan script loads the scripts from dev home dir.
COPY --link --chown=1000:1000 scripts /home/zap/.ZAP_D/scripts/
COPY --link --chown=1000:1000 .xinitrc /home/zap/
COPY --link --chown=1000:1000 firefox /home/zap/.mozilla/firefox/

RUN echo "zap2docker-stable" > /zap/container && \
    chmod a+x /home/zap/.xinitrc

HEALTHCHECK CMD curl --silent --output /dev/null --fail http://localhost:$ZAP_PORT/ || exit 1
