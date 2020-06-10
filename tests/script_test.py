#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test the rest interface."""
import os
from os.path import join, dirname
from importlib import reload
from time import sleep
from multiprocessing import Process
from cherrypy.test import helper
import celery_setup_test

os.environ['SCRIPT_DIR'] = os.path.join(os.path.dirname(__file__), '..', 'contrib', 'example', 'scripts')
reload(celery_setup_test)


def _cli_entrypoint(*argv):
    # pylint: disable=import-outside-toplevel
    from pacifica.cli.__main__ import main as cli_main
    os.chdir(join(dirname(__file__)))
    return cli_main(argv)


def _call_cli(*argv):
    cli_proc = Process(target=_cli_entrypoint, args=argv, name='pacifica-cli')
    cli_proc.start()
    cli_proc.join()
    return cli_proc.exitcode


class DispatcherK8STest(celery_setup_test.TestDispatcherK8SBase, helper.CPWebCase):
    """Base class for all testing classes."""

    def test_happy_path(self):
        """Test a default summation in example."""
        # pylint: disable=import-outside-toplevel
        from pacifica.dispatcher_k8s.orm import ScriptLog
        return_code = _call_cli('pacifica-cli', 'upload', '--logon', 'dmlb2001', 'uploader.json')
        self.assertEqual(return_code, 0, 'return code wasn\'t zero {}'.format(return_code))
        sleep(10)
        scriptlog = ScriptLog.get()
        self.assertEqual(scriptlog.return_code, '0', 'Script should return 0')
