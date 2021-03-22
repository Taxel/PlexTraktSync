FROM python:3.9-alpine3.13 AS base

FROM base AS build

WORKDIR /app
ENTRYPOINT ["/app/main.py"]

# Install app depedencies
RUN pip install pipenv
COPY Pipfile* ./
RUN pipenv install --system --deploy

# Copy rest of the app
COPY . .

# https://stackoverflow.com/a/32557094/2314626
# docker build --target=sourceless .
FROM build AS sourceless
ENTRYPOINT ["python", "/app/main.pyc"]
RUN python -m compileall -b .
RUN find -name '*.py' -delete

# plain image, with source code
FROM build AS runtime
