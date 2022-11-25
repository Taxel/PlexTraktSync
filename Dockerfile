# syntax = docker/dockerfile:1.3-labs
FROM python:3.11-alpine3.16 AS base

WORKDIR /app

# Install app dependencies
FROM base AS build
RUN pip install pipenv
COPY Pipfile* ./
RUN pipenv install --deploy

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
ENTRYPOINT ["python", "-m", "plextraktsync"]

ENV \
	PATH=/root/.local/bin:$PATH \
	PTS_CONFIG_DIR=/app/config \
	PTS_CACHE_DIR=/app/config \
	PTS_LOG_DIR=/app/config \
	PTS_IN_DOCKER=1 \
	PYTHONUNBUFFERED=1

VOLUME /app/config

# Copy things together
COPY --from=build /root/.local/share/virtualenvs/app-*/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=compile /app ./
RUN ln -s /app/plextraktsync.sh /usr/bin/plextraktsync
# https://github.com/python/cpython/issues/69667
RUN chmod a+x /root
