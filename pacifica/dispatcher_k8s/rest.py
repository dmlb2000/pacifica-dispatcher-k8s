#!/usr/bin/python
# -*- coding: utf-8 -*-
"""CherryPy module containing classes for rest interface."""
from json import dumps
import cherrypy
from .tasks import CELERY_APP
from .dispatcher import ReceiveTaskModel


def error_page_default(**kwargs):
    """The default error page should always enforce json."""
    cherrypy.response.headers['Content-Type'] = 'application/json'
    return dumps({
        'status': kwargs['status'],
        'message': kwargs['message'],
        'traceback': kwargs['traceback'],
        'version': kwargs['version']
    })


application = ReceiveTaskModel.create_cherrypy_app(CELERY_APP.tasks['pacifica.dispatcher.tasks.receive'])
