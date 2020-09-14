#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Configuration reading and validation module."""
from os import getenv, scandir, access, X_OK
from os.path import join, isdir
from argparse import Namespace
from configparser import ConfigParser
from .globals import CONFIG_FILE


def get_local_scripts(script_dir):
    """Read script dir and return executable files."""
    exe_scripts = []
    if isdir(script_dir):
        with scandir(script_dir) as entry_it:
            for entry in sorted(entry_it, key=lambda o: o.name):
                if not entry.name.startswith('.') and entry.is_file() and access(join(script_dir, entry.name), X_OK):
                    exe_scripts.append(entry.name)
    return exe_scripts


def get_config():
    """Return the ConfigParser object with defaults set."""
    configparser = ConfigParser(allow_no_value=True)
    configparser.add_section('endpoints')
    configparser.set('endpoints', 'ca_bundle', 'True')
    configparser.add_section('authentication')
    configparser.set('authentication', 'type', getenv(
        'AUTHENTICATION_TYPE', 'basic'))
    configparser.set('authentication', 'username', getenv(
        'AUTHENTICATION_USERNAME', ''))
    configparser.set('authentication', 'password', getenv(
        'AUTHENTICATION_PASSWORD', ''))
    configparser.add_section('database')
    configparser.set('database', 'peewee_url', getenv(
        'PEEWEE_URL', 'sqlite:///db.sqlite3'))
    configparser.add_section('celery')
    configparser.set('celery', 'broker_directory', getenv(
        'BROKER_DIRECTORY', 'broker'))
    configparser.add_section('dispatcher_k8s')
    configparser.set('dispatcher_k8s', 'self_url', getenv(
        'SELF_URL', 'http://localhost:8069/receive'))
    configparser.set('dispatcher_k8s', 'subscription_jsonpath', getenv(
        'JSONPATH', '$.data'))
    configparser.set('dispatcher_k8s', 'script_dir', getenv(
        'SCRIPT_DIR', '/scripts.d'))
    configparser.set('dispatcher_k8s', 'data_dir', getenv(
        'DATA_DIR', '/data'))
    configparser.add_section('dispatcher_k8s_scripts')
    configparser.read(CONFIG_FILE)
    local_scripts = get_local_scripts(configparser.get('dispatcher_k8s', 'script_dir'))

    def _script_defaults(script):
        configparser.set('dispatcher_k8s_scripts', script, '')
        configparser.add_section(script)
        if not configparser.get(script, 'router_jsonpath'):
            configparser.set(script, 'router_jsonpath', """$[?(
                $["data"][*][?(
                    @["destinationTable"] = "TransactionKeyValue"
                        and
                    @["key"] = "do_processing"
                        and
                    @["value"] = "True"
                )]
            )]""")
        if not configparser.get(script, 'script_file'):
            configparser.set(script, 'script_file', 'run')
        section_str = '{}:output_dirs'.format(script)
        configparser.add_section(section_str)
        if not configparser.options(section_str):
            configparser.set(section_str, 'output', '')
        for output_dir in configparser.options(section_str):
            section_str = '{}:{}'.format(script, output_dir)
            configparser.add_section(section_str)
            if not configparser.get(section_str, 'directory'):
                configparser.set(section_str, 'directory', output_dir)
            if not configparser.get(section_str, 'key_value_file'):
                configparser.set(section_str, 'key_value_file', 'kvp.csv')
            if not configparser.get(section_str, 'key_value_parser'):
                configparser.set(section_str, 'key_value_parser', 'csv')
    if local_scripts:
        for script in local_scripts:
            _script_defaults(script)
    else:
        _script_defaults('run')
    return configparser


def get_script_config(configparser, script):
    """Get script config namespace."""
    output_dirs = []
    if configparser.has_section('{}:output_dirs'.format(script)):
        output_config = configparser.options('{}:output_dirs'.format(script))
    else:
        output_config = ['output']
    for output_dir in output_config:
        section_str = '{}:{}'.format(script, output_dir)
        output_dirs.append(Namespace(
            directory=configparser.get(section_str, 'directory'),
            kvfile=configparser.get(section_str, 'key_value_file'),
            kvparser=configparser.get(section_str, 'key_value_parser')
        ))
    return Namespace(
        router_jsonpath=configparser.get(script, 'router_jsonpath'),
        script_id=script,
        script=configparser.get(script, 'script_file'),
        script_dir=configparser.get('dispatcher_k8s', 'script_dir'),
        data_dir=configparser.get('dispatcher_k8s', 'data_dir'),
        output_dirs=output_dirs
    )
