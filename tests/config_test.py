#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test the rest interface."""
from os import environ
from os.path import dirname, join
from unittest import TestCase
from pacifica.dispatcher_k8s.config import get_config


class DispatcherConfigTest(TestCase):
    """Base class for all testing classes."""

    def test_empty_scriptdir(self):
        """Test a default summation in example."""
        environ['SCRIPT_DIR'] = join(dirname(__file__), 'script_dirs', 'empty')
        config = get_config()
        self.assertTrue('run' in config['dispatcher_k8s_scripts'], 'run should be in scripts')
        del environ['SCRIPT_DIR']

    def test_two_scriptdir(self):
        """Test a default summation in example."""
        environ['SCRIPT_DIR'] = join(dirname(__file__), 'script_dirs', 'two_scripts')
        config = get_config()
        self.assertTrue('script1' in config['dispatcher_k8s_scripts'], 'script1 should be in scripts')
        self.assertTrue('script2' in config['dispatcher_k8s_scripts'], 'script2 should be in scripts')
        self.assertTrue('run' not in config['dispatcher_k8s_scripts'], 'run should not be in scripts')
        del environ['SCRIPT_DIR']
