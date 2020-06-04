#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test the rest interface."""
import os
from os.path import join, dirname
from time import sleep
import requests
from cherrypy.test import helper
from pacifica.cli.__main__ import main as cli_main
from .celery_setup_test import TestDispatcherK8SBase


class DispatcherK8STest(TestDispatcherK8SBase, helper.CPWebCase):
    """Base class for all testing classes."""

    def test_default_mul(self):
        """Test a default summation in example."""
        return_code = cli_main(['pacifica-cli', 'upload', '--logon', 'dmlb2001', 'uploader.json'])
        self.assertEqual(return_code, 0, 'return code wasn\'t zero {}'.format(return_code))
        sleep(30)
        
