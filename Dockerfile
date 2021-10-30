FROM python:3.10-alpine3.13 AS base
WORKDIR /app

# Install app depedencies
FROM base AS build
RUN pip install pipenv
COPY Pipfile* ./
RUN pipenv install --deploy

# Create __version__ from $APP_VERSION
FROM base AS version
ARG APP_VERSION=$APP_VERSION
ENV APP_VERSION=$APP_VERSION

RUN mkdir -p /app/plex_trakt_sync
RUN echo "__version__ = '$APP_VERSION'" > plex_trakt_sync/__init__.py
RUN cat plex_trakt_sync/__init__.py
RUN python -c "from plex_trakt_sync import __version__; print(__version__)"

FROM base
ENTRYPOINT ["python", "-m", "plex_trakt_sync"]

ENV \
	PTS_CONFIG_DIR=/app/config \
	PTS_CACHE_DIR=/app/config \
	PTS_LOG_DIR=/app/config \
	PTS_IN_DOCKER=1 \
	PYTHONUNBUFFERED=1

VOLUME /app/config

# Copy things together
COPY plex_trakt_sync ./plex_trakt_sync/
COPY --from=version /app/plex_trakt_sync/__init__.py plex_trakt_sync/
COPY --from=build /root/.local/share/virtualenvs/app-*/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
