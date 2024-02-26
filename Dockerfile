FROM python:latest-alpine

COPY requirements.txt /tmp/requirements.txt

RUN pip install -U pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY . ./src

WORKDIR /src