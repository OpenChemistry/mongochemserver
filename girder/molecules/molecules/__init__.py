# -*- coding: utf-8 -*-

from .molecule import Molecule
from .calculation import Calculation
from .experiment import Experiment
from girder import events
from girder.models.model_base import ValidationException
from girder.utility.model_importer import ModelImporter
from .constants import PluginSettings
from girder.utility import setting_utilities

from .models.calculation import Calculation as CalculationModel
from .models.cubecache import Cubecache as CubecacheModel
from .models.experimental import Experimental as ExperimentalModel
from .models.molecule import Molecule as MoleculeModel

from girder.plugin import GirderPlugin


@setting_utilities.validator({
    PluginSettings.VIRTUOSO_BASE_URL,
    PluginSettings.VIRTUOSO_RDF_UPLOAD_PATH,
    PluginSettings.VIRTUOSO_USER,
    PluginSettings.SEMANTIC_URI_BASE,
    PluginSettings.VIRTUOSO_PASSWORD,
    PluginSettings.JENA_BASE_URL,
    PluginSettings.JENA_USER,
    PluginSettings.JENA_PASSWORD,
    PluginSettings.JENA_DATASET,
    PluginSettings.OPENBABEL_BASE_URL,
    PluginSettings.AVOGADRO_BASE_URL
})
def validateSettings(event):
    pass


class MoleculesPlugin(GirderPlugin):
    DISPLAY_NAME = 'Molecular Data'


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
                    validateSettings)
