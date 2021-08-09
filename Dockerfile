FROM python:3.9-alpine3.13 AS base

WORKDIR /app
ENTRYPOINT ["python", "-m", "plex_trakt_sync"]

# Install app depedencies
RUN pip install --no-cache-dir pipenv
COPY Pipfile* ./
RUN pipenv install --system --deploy

# Copy rest of the app
COPY . .
