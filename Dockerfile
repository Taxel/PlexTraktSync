FROM python:3.7.9-slim

COPY ./app/requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt
COPY ./app/*.py /app/

WORKDIR /app
ENTRYPOINT ["python3","main.py"]