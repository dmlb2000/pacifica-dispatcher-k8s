#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test the rest interface."""
from unittest import TestCase
from pacifica.dispatcher_k8s.__main__ import main as cmd_main


class DispatcherCmdTest(TestCase):
    """Base class for all testing classes."""

    def test_happy_path(self):
        """Test a default summation in example."""
        return_code = cmd_main(['pacifica-dispatcher-cmd', '--stop-after-a-moment'])
        self.assertEqual(return_code, 0, 'return code wasn\'t zero {}'.format(return_code))
