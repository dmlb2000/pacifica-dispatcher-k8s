#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Global configuration options expressed in environment variables."""
from os import getenv
from os.path import join

CONFIG_FILE = getenv(
    'DISPATCHER_K8S_CONFIG',
    join('', 'etc', 'pacifica-dispatcher-k8s', 'config.ini')
)
