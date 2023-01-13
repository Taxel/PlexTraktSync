# syntax = docker/dockerfile:1.3-labs
FROM python:3.11-alpine3.16 AS base
WORKDIR /app

# Create minimal layer with extra tools
FROM base AS tools
RUN apk add util-linux shadow
WORKDIR /dist
RUN <<eot
install -d ./usr/bin ./usr/lib
install -p /usr/bin/setpriv ./usr/bin
install -p /usr/lib/libcap-ng.so.0 ./usr/lib
install -p /usr/sbin/usermod /usr/sbin/groupmod ./usr/bin
eot

FROM base AS wheels
# Download wheels/sources
RUN \
	--mount=type=cache,id=pip,target=/root/.cache/pip \
	--mount=type=bind,source=./requirements.txt,target=./requirements.txt \
	pip download --dest /wheels -r requirements.txt
# Build missing wheels
RUN \
	--mount=type=cache,id=pip,target=/root/.cache/pip \
	pip wheel $(ls /wheels/*.gz /wheels/*.zip 2>/dev/null) --wheel-dir=/wheels

# Install app dependencies
FROM base AS build
RUN apk add git
RUN pip install pipenv
RUN \
	--mount=type=bind,from=wheels,source=/wheels,target=/wheels \
	pipenv run pip install /wheels/*.whl

FROM base AS compile
ARG APP_VERSION=$APP_VERSION
ENV APP_VERSION=$APP_VERSION

COPY plextraktsync ./plextraktsync/
COPY plextraktsync.sh .
# Create __version__ from $APP_VERSION
RUN echo "__version__ = '${APP_VERSION:-unknown}'" > plextraktsync/__init__.py
RUN cat plextraktsync/__init__.py
RUN python -c "from plextraktsync import __version__; print(__version__)"

# Compile sources
RUN python -m compileall .
RUN chmod -R a+rX,g-w .

FROM base
ENTRYPOINT ["/init"]

ENV \
	PATH=/root/.local/bin:$PATH \
	PTS_CONFIG_DIR=/app/config \
	PTS_CACHE_DIR=/app/config \
	PTS_LOG_DIR=/app/config \
	PTS_IN_DOCKER=1 \
	PYTHONUNBUFFERED=1

VOLUME /app/config

# Add user/group
RUN <<eot
	set -x
	addgroup --gid 1000 --system plextraktsync
	adduser \
		--disabled-password \
		--gecos "Plex Trakt Sync" \
		--home "$(pwd)" \
		--ingroup plextraktsync \
		--no-create-home \
		--uid 1000 \
		plextraktsync
eot

# Copy things together
COPY --from=tools /dist /
COPY --from=build /root/.local/share/virtualenvs/app-*/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=compile /app ./
COPY entrypoint.sh /init
RUN ln -s /app/plextraktsync.sh /usr/bin/plextraktsync
# https://github.com/python/cpython/issues/69667
RUN chmod a+x /root
