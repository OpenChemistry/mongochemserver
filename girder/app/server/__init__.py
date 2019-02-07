from .configuration import Configuration
from girder.utility import setting_utilities
from .constants import Features


@setting_utilities.validator({
    Features.NOTEBOOKS
})
def validateSettings(event):
    pass

def load(info):
    info['apiRoot'].configuration = Configuration()
