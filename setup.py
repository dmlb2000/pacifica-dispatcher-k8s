#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Setup and install the pacifica service."""
from os import path
from setuptools import setup, find_packages


setup(
    name='pacifica-dispatcher-k8s',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description='Pacifica Dispatcher for Kubernetes',
    url='https://github.com/pacifica/pacifica-dispatcher-k8s/',
    long_description=open(path.join(
        path.abspath(path.dirname(__file__)),
        'README.md')).read(),
    long_description_content_type='text/markdown',
    author='David Brown',
    author_email='dmlb2000@gmail.com',
    packages=find_packages(),
    namespace_packages=['pacifica'],
    entry_points={
        'console_scripts': [
            'pacifica-dispatcher-k8s=pacifica.dispatcher_k8s.__main__:main'
        ]
    },
    install_requires=[
        'celery',
        'cherrypy',
        'peewee',
        'pacifica-cli',
        'pacifica-dispatcher',
        'eventlet'
    ]
)
