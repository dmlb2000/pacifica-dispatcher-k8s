#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The Celery tasks module."""
from .config import get_config
from .dispatcher import ReceiveTaskModel, ROUTER

CELERY_APP = ReceiveTaskModel.create_celery_app(
    ROUTER,
    'pacifica.dispatcher_k8s.app',
    'pacifica.dispatcher_k8s.tasks.receive',
    backend=get_config().get('celery', 'backend_url'),
    broker=get_config().get('celery', 'broker_url')
)
