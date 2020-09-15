#!/usr/bin/python
# -*- coding: utf-8 -*-
"""CherryPy module containing classes for rest interface."""
from json import dumps
import cherrypy
import peewee
from .tasks import celery_app
from .dispatcher import ReceiveTaskModel
from .orm import ScriptLog, ScriptLogEncoder


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


def json_handler(*args, **kwargs):
    """Encode the ScriptLog object to json."""
    # pylint: disable=protected-access
    value = cherrypy.serving.request._json_inner_handler(*args, **kwargs)
    return dumps(value, cls=ScriptLogEncoder).encode('utf-8')

# pylint: disable=too-few-public-methods


class ScriptLogRest:
    """Endpoint for interacting with ScriptLog db entries."""

    exposed = True

    # pylint: disable=invalid-name
    # pylint: disable=no-self-use
    @cherrypy.tools.json_out(handler=json_handler)
    def GET(self, uuid=None):
        """Get a scriptlog db entry or all of them."""
        if uuid:
            try:
                return ScriptLog.select().where(ScriptLog.uuid == uuid).dicts().get()
            except peewee.DoesNotExist as ex:
                raise cherrypy.HTTPError(404, 'No Such ScriptLog') from ex
        return list(ScriptLog.select().dicts())


cherrypy.tree.mount(ScriptLogRest(), '/scriptlog', config=app_config)
application = ReceiveTaskModel.create_cherrypy_app(celery_app.tasks['pacifica.dispatcher_k8s.tasks.receive'])
