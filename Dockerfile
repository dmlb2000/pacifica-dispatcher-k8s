FROM python:3.8

WORKDIR /usr/src/dispatcher_k8s
COPY . .
RUN pip install --no-cache-dir . future pacifica-cli
RUN mkdir /data /scripts.d /etc/pacifica-cli
COPY tests/uploader.json /etc/pacifica-cli/uploader.json
WORKDIR /data
EXPOSE 8069
ENTRYPOINT pacifica-dispatcher-k8s
