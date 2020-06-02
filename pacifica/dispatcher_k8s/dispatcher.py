#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Dispatcher Module."""
import playhouse.db_url
from pacifica.dispatcher.receiver import create_peewee_model
from pacifica.dispatcher.router import Router
from .config import get_config

ROUTER = Router()
DB = playhouse.db_url.connect(get_config().get('database', 'peewee_url'))
ReceiveTaskModel = create_peewee_model(DB)
