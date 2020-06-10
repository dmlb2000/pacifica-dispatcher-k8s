#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The Celery tasks module."""
from os import makedirs, getcwd
from os.path import join, isdir, isabs
from .config import get_config
from .dispatcher import ReceiveTaskModel, ROUTER
from .eventhandler import make_routes

_broker_dir = get_config().get('celery', 'broker_directory')
if not isabs(_broker_dir):
    _broker_dir = join(getcwd(), _broker_dir)
CELERY_OPTIONS = {
    'loglevel': 'INFO',
    'traceback': True,
    'broker': 'filesystem://',
    'backend': 'rpc://',
    'broker_transport_options': {
        'data_folder_in': join(_broker_dir, 'out'),
        'data_folder_out': join(_broker_dir, 'out'),
        'data_folder_processed': join(_broker_dir, 'processed')
    },
    'result_persistent': False,
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json']
}

celery_app = ReceiveTaskModel.create_celery_app(
    ROUTER,
    'pacifica.dispatcher_k8s.app',
    'pacifica.dispatcher_k8s.tasks.receive',
    **CELERY_OPTIONS
)
celery_app.conf.update(**CELERY_OPTIONS)
make_routes()


def setup_broker_dir():
    """Setup the broker directories."""
    for _chk_dir in [_broker_dir, join(_broker_dir, 'out'), join(_broker_dir, 'processed')]:
        if not isdir(_chk_dir):
            makedirs(_chk_dir)
