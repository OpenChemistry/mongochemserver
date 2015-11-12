# -*- coding: utf-8 -*-

from .molecule import Molecule
from .calculation import Calculation
from girder import events
from girder.models.model_base import ValidationException
from .constants import PluginSettings


def validateSettings(event):
    if event.info['key'] == PluginSettings.VIRTUOSO_BASE_URL or \
       event.info['key'] == PluginSettings.VIRTUOSO_RDF_UPLOAD_PATH or \
       event.info['key'] == PluginSettings.VIRTUOSO_USER or \
       event.info['key'] == PluginSettings.SEMANTIC_URI_BASE or \
       event.info['key'] == PluginSettings.VIRTUOSO_PASSWORD:
        event.preventDefault().stopPropagation()


def load(info):
    info['apiRoot'].molecules = Molecule()
    info['apiRoot'].calculations = Calculation()
    events.bind('model.setting.validate', 'molecules', validateSettings)
