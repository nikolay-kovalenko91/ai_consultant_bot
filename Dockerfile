FROM python:3.11-alpine

COPY requirements.txt /tmp/requirements.txt

RUN pip install -U pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

ARG SERVICE_NAME
RUN if [ "$SERVICE_NAME" = "telegram_client" ]; then apk update && apk add --no-cache libstdc++ gcompat; fi

COPY . ./src

WORKDIR /src