from .configuration import Configuration
from girder.utility import setting_utilities
from .constants import Features

from girder.plugin import GirderPlugin

@setting_utilities.validator({
    Features.NOTEBOOKS
})

class OpenChemistryAppPlugin(GirderPlugin):
    DISPLAY_NAME = 'OpenChemistry App'

    def validateSettings(self, event):
        pass

    def load(self, info):
        info['apiRoot'].configuration = Configuration()
