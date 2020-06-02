#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test cart database setup class."""
import os
from time import sleep
from shutil import rmtree
from tempfile import TemporaryDirectory
import threading
import cherrypy
from celery.bin.celery import main as celery_main
from pacifica.dispatcher_k8s.dispatcher import DB, ReceiveTaskModel
from pacifica.dispatcher_k8s.rest import application, error_page_default
from pacifica.dispatcher_k8s.orm import ScriptLog
from pacifica.dispatcher_k8s.config import get_config


class TestDispatcherK8SBase:
    """Contain all the tests for the Cart Interface."""

    PORT = 8069
    HOST = '127.0.0.1'
    url = 'http://{0}:{1}'.format(HOST, PORT)
    headers = {'content-type': 'application/json'}

    @classmethod
    def setup_server(cls):
        """Start all the services."""
        os.environ['SCRIPT_DIR'] = os.path.join(os.path.dirname(__file__), '..', 'contrib', 'example', 'scripts')
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
        # pylint: enable=no-member

        self.data_dir_name = TemporaryDirectory().name
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
