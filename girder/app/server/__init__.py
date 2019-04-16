from .configuration import Configuration
from girder.utility import setting_utilities
from .constants import Features, Deployment


@setting_utilities.validator({
    Features.NOTEBOOKS,
    Deployment.SITE
})
def validateSettings(event):
    pass

def load(info):
    info['apiRoot'].configuration = Configuration()
