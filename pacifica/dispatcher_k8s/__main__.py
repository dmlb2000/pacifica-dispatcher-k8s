#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The main module for executing the CherryPy server."""
from __future__ import absolute_import, unicode_literals
from sys import argv as sys_argv
from time import sleep
from signal import signal, SIGTERM
from argparse import ArgumentParser, SUPPRESS
from threading import Thread
from multiprocessing import Process
import cherrypy
from celery.bin import worker as celery_worker
from .orm import database_setup
from .rest import application, error_page_default, app_config
from .globals import CONFIG_FILE
from .tasks import celery_app, CELERY_OPTIONS, setup_broker_dir


def stop_later(doit, cherrypy_proc, celery_proc):
    """Used for unit testing stop after 60 seconds."""
    if not doit:  # pragma: no cover
        return

    def sleep_then_exit():
        """
        Sleep for 20 seconds then call cherrypy exit.

        Hopefully this is long enough for the end-to-end tests to finish
        """
        sleep(20)
        cherrypy_proc.terminate()
        celery_proc.terminate()
        cherrypy_proc.join()
        celery_proc.join()
    sleep_thread = Thread(target=sleep_then_exit)
    sleep_thread.daemon = True
    sleep_thread.start()


def run_celery_worker():
    """Run the main solo worker."""
    worker = celery_worker.worker(app=celery_app)
    return worker.run(**CELERY_OPTIONS)


def run_cherrypy_server(args):
    """Run the main cherrypy quickstart."""
    cherrypy.config.update({
        'error_page.default': error_page_default,
        'server.socket_host': args.address,
        'server.socket_port': args.port,
        'engine.autoreload.on': False
    })
    return cherrypy.quickstart(application, '/', config=app_config)


def main(argv=None):
    """Main method to start the httpd server."""
    parser = ArgumentParser(description='Run the notifications server.')
    parser.add_argument('-c', '--config', metavar='CONFIG', type=str,
                        default=CONFIG_FILE, dest='config',
                        help='cherrypy config file')
    parser.add_argument('-p', '--port', metavar='PORT', type=int,
                        default=8069, dest='port',
                        help='port to listen on')
    parser.add_argument('-a', '--address', metavar='ADDRESS',
                        default='0.0.0.0', dest='address',
                        help='address to listen on')
    parser.add_argument('--stop-after-a-moment', help=SUPPRESS,
                        default=False, dest='stop_later',
                        action='store_true')
    if argv is None:  # pragma: no cover
        args = parser.parse_args(sys_argv[1:])
    else:
        args = parser.parse_args(argv)
    database_setup()
    setup_broker_dir()
    cherrypy_proc = Process(target=run_cherrypy_server, args=(args,), name='cherrypy')
    celery_proc = Process(target=run_celery_worker, name='celery')
    cherrypy_proc.start()
    celery_proc.start()

    def _term_procs():  # pragma: no cover cmd line Ctrl-C
        cherrypy_proc.terminate()
        celery_proc.terminate()
        cherrypy_proc.join()
        celery_proc.join()
    signal(SIGTERM, _term_procs)
    stop_later(args.stop_later, cherrypy_proc, celery_proc)
    cherrypy_proc.join()
    celery_proc.join()
    return 0
