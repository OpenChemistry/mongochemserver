from .configuration import Configuration
from girder.utility import setting_utilities
from .constants import Features, Branding, Deployment

from girder.plugin import GirderPlugin

@setting_utilities.validator({
    Features.NOTEBOOKS,
    Deployment.SITE,
    Branding.PRIVACY,
    Branding.LICENSE,
    Branding.HEADER_LOGO_ID,
    Branding.FOOTER_LOGO_ID,
    Branding.FOOTER_LOGO_URL,
    Branding.FAVICON_ID
})
def validateSettings(event):
    pass

class AppPlugin(GirderPlugin):
    DISPLAY_NAME = 'OpenChemistry App'

    def load(self, info):
        info['apiRoot'].configuration = Configuration()
