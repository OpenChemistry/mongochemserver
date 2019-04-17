from .configuration import Configuration
from girder.utility import setting_utilities
from .constants import Features, Branding, Deployment


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

def load(info):
    info['apiRoot'].configuration = Configuration()
