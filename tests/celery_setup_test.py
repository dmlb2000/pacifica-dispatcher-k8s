#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test cart database setup class."""
import os
from time import sleep
from shutil import rmtree
from multiprocessing import Process
import cherrypy
import requests


_data_dir_name = os.path.join(os.path.dirname(__file__), 'datadir')
os.environ['DATA_DIR'] = _data_dir_name
os.environ['BROKER_DIRECTORY'] = os.path.join(_data_dir_name, 'broker')
os.environ['UPLOAD_URL'] = 'http://localhost:8066/upload'
os.environ['UPLOAD_STATUS_URL'] = 'http://localhost:8066/get_state'
os.environ['UPLOAD_POLICY_URL'] = 'http://localhost:8181/uploader'
os.environ['UPLOAD_VALIDATION_URL'] = 'http://localhost:8181/ingest'
os.environ['DOWNLOAD_URL'] = 'http://localhost:8081'
os.environ['DOWNLOAD_POLICY_URL'] = 'http://localhost:8181/status/transactions/by_id'
os.environ['AUTHENTICATION_TYPE'] = 'None'
os.environ['UPLOADER_CONFIG'] = os.path.join(os.path.dirname(__file__), 'uploader.json')


def run_celery_worker():
    """Run the main solo worker."""
    # pylint: disable=import-outside-toplevel
    from pacifica.dispatcher_k8s.tasks import celery_app, CELERY_OPTIONS
    from celery.bin import worker as celery_worker
    CELERY_OPTIONS['pool'] = 'solo'
    CELERY_OPTIONS['concurrency'] = 1
    worker = celery_worker.worker(app=celery_app)
    return worker.run(**CELERY_OPTIONS)


class TestDispatcherK8SBase:
    """Contain all the tests for the Cart Interface."""

    PORT = 8069
    HOST = '127.0.0.1'
    url = 'http://{0}:{1}'.format(HOST, PORT)
    headers = {'content-type': 'application/json'}

    # pylint: disable=invalid-name
    @classmethod
    def setUpClass(cls):
        """Create a subscription and save it to the class."""
        notify_url = os.getenv('NOTIFY_URL', 'http://localhost:8070')
        self_url = os.getenv('SELF_URL', 'http://localhost:8069')
        remote_user = os.getenv('REMOTE_USER', 'dmlb2001')
        resp = requests.post(
            '{}/eventmatch'.format(notify_url),
            headers={'Http-Remote-User': remote_user},
            json={
                'name': 'My Event Match',
                'jsonpath': """
                    $[?(
                        @["cloudEventsVersion"] = "0.1" and
                        @["eventType"] = "org.pacifica.metadata.ingest"
                )]
                """,
                'target_url': '{}/receive'.format(self_url)
            }
        )
        assert resp.status_code == 200
        cls.subscription_uuid = resp.json()['uuid']

    # pylint: disable=invalid-name
    @classmethod
    def tearDownClass(cls):
        """Delete the notification subscription."""
        notify_url = os.getenv('NOTIFY_URL', 'http://localhost:8070')
        remote_user = os.getenv('REMOTE_USER', 'dmlb2001')
        resp = requests.delete(
            '{}/eventmatch/{}'.format(notify_url, cls.subscription_uuid),
            headers={'Http-Remote-User': remote_user}
        )
        assert resp.status_code == 200

    @classmethod
    def setup_server(cls):
        """Start all the services."""
        # pylint: disable=import-outside-toplevel
        from pacifica.dispatcher_k8s.tasks import setup_broker_dir
        from pacifica.dispatcher_k8s.rest import application, app_config
        setup_broker_dir()
        cherrypy.config.update({
            'server.socket_host': cls.HOST,
            'server.socket_port': cls.PORT
        })
        cherrypy.tree.mount(application, '/', config=app_config)

    # pylint: disable=invalid-name
    def setUp(self):
        """Setup the database with in memory sqlite."""
        # pylint: disable=import-outside-toplevel
        from pacifica.dispatcher_k8s.tasks import setup_broker_dir
        from pacifica.dispatcher_k8s.dispatcher import DB, ReceiveTaskModel
        from pacifica.dispatcher_k8s.orm import ScriptLog, database_setup
        setup_broker_dir()
        DB.drop_tables([ScriptLog, ReceiveTaskModel])
        database_setup()
        self.celery_proc = Process(target=run_celery_worker, name='celery')
        self.celery_proc.start()
        sleep(3)

    # pylint: disable=invalid-name
    def tearDown(self):
        """Tear down the test and remove local state."""
        self.celery_proc.kill()
        self.celery_proc.join()
        rmtree(_data_dir_name)
