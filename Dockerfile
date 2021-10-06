FROM python:3.10-alpine3.13 AS base

WORKDIR /app
ENTRYPOINT ["python", "-m", "plex_trakt_sync"]

# Install app depedencies
RUN pip install --no-cache-dir pipenv
COPY Pipfile* ./
RUN pipenv install --system --deploy

ENV \
	PTS_CONFIG_DIR=/app/config \
	PTS_CACHE_DIR=/app/config \
	PTS_LOG_DIR=/app/config \
	PTS_IN_DOCKER=1 \
	PYTHONUNBUFFERED=1

VOLUME /app/config

# Copy rest of the app
COPY . .
ARG APP_VERSION=$APP_VERSION
ENV APP_VERSION=$APP_VERSION
