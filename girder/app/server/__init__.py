from .configuration import Configuration
from girder.utility import setting_utilities
from .constants import Features, Configuration as Conf


@setting_utilities.validator({
    Features.NOTEBOOKS,
    Conf.PRIVACY,
    Conf.LICENSE,
    Conf.HEADER_LOGO_ID,
    Conf.FOOTER_LOGO_ID,
    Conf.FOOTER_LOGO_URL,
    Conf.FAVICON_ID
})
def validateSettings(event):
    pass

def load(info):
    info['apiRoot'].configuration = Configuration()
