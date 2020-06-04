#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test cart database setup class."""
import os
from time import sleep
from shutil import rmtree
from tempfile import TemporaryDirectory
import threading
import cherrypy
import requests
from celery.bin.celery import main as celery_main
from pacifica.dispatcher_k8s.dispatcher import DB, ReceiveTaskModel
from pacifica.dispatcher_k8s.rest import application, error_page_default
from pacifica.dispatcher_k8s.orm import ScriptLog, database_setup
from pacifica.dispatcher_k8s.config import get_config


class TestDispatcherK8SBase:
    """Contain all the tests for the Cart Interface."""

    PORT = 8069
    HOST = '127.0.0.1'
    url = 'http://{0}:{1}'.format(HOST, PORT)
    headers = {'content-type': 'application/json'}

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
                "name": "My Event Match",
                "jsonpath": """
                    $[?(
                        @["cloudEventsVersion"] = "0.1" and
                        @["eventType"] = "org.pacifica.metadata.ingest"
                )]
                """,
                "target_url": "{}/receive".format(self_url)
            }
        )
        assert resp.status_code == 200
        cls.subscription_uuid = resp.json()['uuid']

    @classmethod
    def tearDownClass(cls):
        """Delete the notification subscription."""
        notify_url = os.getenv('NOTIFY_URL', 'http://localhost:8070')
        remote_user = os.getenv('REMOTE_USER', 'dmlb2001')
        resp = requests.delete(
            '{}/eventmatch/{}'.format(notify_url, cls.subscription_uuid)
        )
        assert resp.status_code == 403

    @classmethod
    def setup_server(cls):
        """Start all the services."""
        os.environ['SCRIPT_DIR'] = os.path.join(os.path.dirname(__file__), '..', 'contrib', 'example', 'scripts')
        os.environ['UPLOAD_URL'] = 'http://localhost:8066/upload'
        os.environ['UPLOAD_STATUS_URL'] = 'http://localhost:8066/get_state'
        os.environ['UPLOAD_POLICY_URL'] = 'http://localhost:8181/uploader'
        os.environ['UPLOAD_VALIDATION_URL'] = 'http://localhost:8181/ingest'
        os.environ['DOWNLOAD_URL'] = 'http://localhost:8081'
        os.environ['DOWNLOAD_POLICY_URL'] = 'http://localhost:8181/status/transactions/by_id'
        os.environ['AUTHENTICATION_TYPE'] = 'None'
        os.environ['UPLOADER_CONFIG'] = os.path.join(os.path.dirname(__file__), 'uploader.json')
        cherrypy.config.update({
            'server.socket_host': cls.HOST,
            'server.socket_port': cls.PORT
        })
        cherrypy.tree.mount(application, '/', config={
            '/': {
                'error_page.default': error_page_default,
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            }
        })

    # pylint: disable=invalid-name
    def setUp(self):
        """Setup the database with in memory sqlite."""
        # pylint: disable=protected-access
        # pylint: disable=no-member
        DB.drop_tables([ScriptLog, ReceiveTaskModel])
        database_setup()
        # pylint: enable=no-member

        self.data_dir_name = TemporaryDirectory().name
        os.mkdir(self.data_dir_name)
        os.environ['DATA_DIR'] = self.data_dir_name

        def run_celery_worker():
            """Run the main solo worker."""
            return celery_main([
                'celery', '-A', 'pacifica.dispatcher_k8s.tasks', 'worker', '--pool', 'solo',
                '--quiet', '-b', get_config().get('celery', 'broker_url')
            ])

        self.celery_thread = threading.Thread(target=run_celery_worker)
        self.celery_thread.start()
        print('Done Starting Celery')
        sleep(3)

    # pylint: disable=invalid-name
    def tearDown(self):
        """Tear down the test and remove local state."""
        try:
            celery_main([
                'celery', '-A', 'pacifica.dispatcher_k8s.tasks', 'control',
                '-b', get_config().get('celery', 'broker_url'), 'shutdown'
            ])
        except SystemExit:
            pass
        self.celery_thread.join()
        try:
            celery_main([
                'celery', '-A', 'pacifica.dispatcher_k8s.tasks',
                '-b', get_config().get('celery', 'broker_url'),
                '--force', 'purge'
            ])
        except SystemExit:
            pass
        rmtree(self.data_dir_name)
