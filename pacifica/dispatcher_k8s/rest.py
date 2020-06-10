#!/usr/bin/python
# -*- coding: utf-8 -*-
"""CherryPy module containing classes for rest interface."""
from json import dumps
import cherrypy
from .tasks import celery_app
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


app_config = {
    '/': {
        'error_page.default': error_page_default,
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
    }
}
application = ReceiveTaskModel.create_cherrypy_app(celery_app.tasks['pacifica.dispatcher_k8s.tasks.receive'])
