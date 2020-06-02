#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test the rest interface."""
from time import sleep
import requests
from cherrypy.test import helper
from .celery_setup_test import TestDispatcherK8SBase


class DispatcherK8STest(TestDispatcherK8SBase, helper.CPWebCase):
    """Base class for all testing classes."""

    def test_default_mul(self):
        """Test a default summation in example."""
        resp = requests.get('http://127.0.0.1:8069/dispatch/mul/2/2')
        self.assertEqual(resp.status_code, 200)
        uuid = resp.text
        sleep(2)
        resp = requests.get('http://127.0.0.1:8069/status/{}'.format(uuid))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(resp.text), 4)
