FROM python:3.8

WORKDIR /usr/src/dispatcher_k8s
COPY . .
RUN pip install --no-cache-dir .
RUN pip install --no-cache-dir 'celery[eventlet]' eventlet
RUN mkdir /data /scripts.d
WORKDIR /data
EXPOSE 8069
ENTRYPOINT python -m pacifica.dispatcher_k8s
