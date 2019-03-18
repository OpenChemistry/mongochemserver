# -*- coding: utf-8 -*-

from .molecule import Molecule
from .calculation import Calculation
from .experiment import Experiment
from girder import events
from girder.models.model_base import ValidationException
from .constants import PluginSettings
from girder.utility import setting_utilities


@setting_utilities.validator({
    PluginSettings.VIRTUOSO_BASE_URL,
    PluginSettings.VIRTUOSO_RDF_UPLOAD_PATH,
    PluginSettings.VIRTUOSO_USER,
    PluginSettings.SEMANTIC_URI_BASE,
    PluginSettings.VIRTUOSO_PASSWORD,
    PluginSettings.JENA_BASE_URL,
    PluginSettings.JENA_USER,
    PluginSettings.JENA_PASSWORD,
    PluginSettings.JENA_DATASET
})
def validateSettings(event):
    pass

def load(info):
    info['apiRoot'].molecules = Molecule()
    info['apiRoot'].calculations = Calculation()
    info['apiRoot'].experiments = Experiment()
    events.bind('model.setting.validate', 'molecules', validateSettings)
