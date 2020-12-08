FROM python:3-alpine3.10 as base

FROM base as builder
COPY ./requirements.txt /tmp/requirements.txt
RUN apk add tzdata \
 && apk add --virtual .build-deps gcc python3-dev musl-dev\
 && pip3 install --no-warn-script-location --user -r /tmp/requirements.txt

# a multistage build is completely overkill for this project as it makes the resulting image only about 1mb smaller...
FROM base
# copy installed and built packages
COPY --from=builder /root/.local /root/.local
# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

WORKDIR /var/
COPY ./src ./src
COPY ./entry.sh ./entry.sh
COPY ./config/config.json .
RUN chmod +x entry.sh

VOLUME /var/cache

CMD ["./entry.sh"]