# Pacifica Dispatcher Kubernetes
[![Build Status](https://travis-ci.org/pacifica/pacifica-dispatcher-k8s.svg?branch=master)](https://travis-ci.org/pacifica/pacifica-dispatcher-k8s)

The Kubernetes dispatcher is built and designed to be coupled with
the
[dispatcher operator](https://github.com/pacifica/pacifica-dispatcher-operator).
This code interacts with the
[dispatcher library](https://github.com/pacifica/pacifica-dispatcher)
to download data, route events, call a sidecar container, and upload
results all within Kubernetes.

## The Parts

There are several parts to this code as it encompasses
integrating several python libraries together.

 * [PeeWee](http://docs.peewee-orm.com/en/latest/)
 * [CherryPy](https://cherrypy.org/)
 * [Celery](http://www.celeryproject.org/)
 * [Dispatcher](https://github.com/pacifica/pacifica-dispatcher)

For each major library we have integration points in
specific modules to handle configuration of each library.

### PeeWee

The configuration of PeeWee is pulled from an INI file parsed
from an environment variable or command line option. The
configuration in the file is a database
[connection url](http://docs.peewee-orm.com/en/latest/peewee/database.html#connecting-using-a-database-url).

 * [PeeWee Model](pacifica/dispatcher_k8s/orm.py)
 * [Config Parser](pacifica/dispatcher_k8s/config.py)

### CherryPy

The CherryPy configuration has two entrypoints for use. The
WSGI interface and the embedded server through the main
method.

 * [Main Method](pacifica/dispatcher_k8s/__main__.py)
 * [WSGI API](pacifica/dispatcher_k8s/wsgi.py)
 * [CherryPy Objects](pacifica/dispatcher_k8s/rest.py)

### Celery

The Celery tasks are located in their own module and have
an entrypoint from the CherryPy REST objects. The tasks
save state into a PeeWee database that is also accessed
in the CherryPy REST objects.

 * [Tasks](pacifica/dispatcher_k8s/tasks.py)

## Start Up Process

The default way to start up this service is with a shared
SQLite database. The database must be located in the
current working directory of both the celery workers and
the CherryPy web server. The messaging system in
[Travis](.travis.yml) and [Appveyor](appveyor.yml) is
redis, however the default is rabbitmq.

There are three commands needed to start up the services.
Perform these steps in three separate terminals.

 1. `docker-compose up redis postgres`
 2. `celery -A pacifica.dispatcher_k8s.tasks worker -l info`
 3. `python -m pacifica.dispatcher_k8s`

To test working system run the following in bash:

 1. `UUID=$(curl http://127.0.0.1:8069/dispatch/add/2/2)`
 2. `curl http://127.0.0.1:8069/status/$UUID`
