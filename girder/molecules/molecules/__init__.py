# -*- coding: utf-8 -*-

from .molecule import Molecule
from .calculation import Calculation
from .experiment import Experiment
from girder import events
from girder.models.model_base import ValidationException
from girder.utility.model_importer import ModelImporter
from .constants import PluginSettings

from .models.calculation import Calculation as CalculationModel
from .models.cubecache import Cubecache as CubecacheModel
from .models.experimental import Experimental as ExperimentalModel
from .models.molecule import Molecule as MoleculeModel

from girder.plugin import GirderPlugin


class MoleculePlugin(GirderPlugin):
    DISPLAY_NAME = 'Molecular Data'

    def validateSettings(self, event):
        if event.info['key'] == PluginSettings.VIRTUOSO_BASE_URL or \
           event.info['key'] == PluginSettings.VIRTUOSO_RDF_UPLOAD_PATH or \
           event.info['key'] == PluginSettings.VIRTUOSO_USER or \
           event.info['key'] == PluginSettings.SEMANTIC_URI_BASE or \
           event.info['key'] == PluginSettings.VIRTUOSO_PASSWORD:
            event.preventDefault().stopPropagation()


    def load(self, info):
        # Register models for ModelImporter
        ModelImporter.registerModel('calculation', CalculationModel,
                                    'molecules')
        ModelImporter.registerModel('cubecache', CubecacheModel, 'molecules')
        ModelImporter.registerModel('experimental', ExperimentalModel,
                                    'molecules')
        ModelImporter.registerModel('molecule', MoleculeModel, 'molecules')

        info['apiRoot'].molecules = Molecule()
        info['apiRoot'].calculations = Calculation()
        info['apiRoot'].experiments = Experiment()
        events.bind('model.setting.validate', 'molecules',
                    self.validateSettings)
