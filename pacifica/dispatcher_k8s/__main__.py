#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The main module for executing the CherryPy server."""
from sys import argv as sys_argv
from time import sleep
from argparse import ArgumentParser, SUPPRESS
from threading import Thread
import cherrypy
from celery.bin.celery import main as celery_main
from .orm import database_setup
from .rest import application, error_page_default
from .globals import CONFIG_FILE
from .config import get_config
from .eventhandler import make_routes


def stop_later(doit=False):
    """Used for unit testing stop after 60 seconds."""
    if not doit:  # pragma: no cover
        return

    def sleep_then_exit():
        """
        Sleep for 20 seconds then call cherrypy exit.

        Hopefully this is long enough for the end-to-end tests to finish
        """
        sleep(20)
        cherrypy.engine.exit()
    sleep_thread = Thread(target=sleep_then_exit)
    sleep_thread.daemon = True
    sleep_thread.start()


def run_celery_worker():
    """Run the main solo worker."""
    return celery_main([
        'celery', '-A', 'pacifica.dispatcher_k8s.tasks', 'worker', '--pool', 'eventlet',
        '-b', get_config().get('celery', 'broker_url')
    ])


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
        args = parser.parse_args(sys_argv)
    else:
        args = parser.parse_args(argv)
    database_setup()
    stop_later(args.stop_later)
    make_routes()
    celery_thread = Thread(target=run_celery_worker)
    celery_thread.start()
    cherrypy.config.update({'error_page.default': error_page_default})
    cherrypy.config.update({
        'server.socket_host': args.address,
        'server.socket_port': args.port
    })
    cherrypy.tree.mount(application, '/', config={
        '/': {
            'error_page.default': error_page_default,
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        }
    })
    cherrypy.engine.start()
    cherrypy.engine.block()
    try:
        celery_main([
            'celery', '-A', 'pacifica.dispatcher_k8s.tasks', 'control',
            '-b', get_config().get('celery', 'broker_url'), 'shutdown'
        ])
    except SystemExit:
        pass
    celery_thread.join()


if __name__ == '__main__':
    main()
