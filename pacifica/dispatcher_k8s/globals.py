#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Global configuration options expressed in environment variables."""
from os import getenv
from os.path import join, sep

CONFIG_FILE = getenv(
    'DISPATCHER_K8S_CONFIG',
    '{}{}'.format(sep, join('etc', 'pacifica-dispatcher-k8s', 'config.ini'))
)
