from .configuration import Configuration
from girder.utility import setting_utilities
from .constants import Features

from girder.plugin import GirderPlugin

@setting_utilities.validator({
    Features.NOTEBOOKS
})
def validateSettings(event):
    pass

class AppPlugin(GirderPlugin):
    DISPLAY_NAME = 'OpenChemistry App'

    def load(self, info):
        info['apiRoot'].configuration = Configuration()
