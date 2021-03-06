from .configuration import Configuration
from girder.api.rest import Resource
from girder.utility import setting_utilities
from .constants import Features, Branding, Deployment

from .launch_taskflow import launch_taskflow_endpoint
from .user import get_orcid, set_orcid, get_twitter, set_twitter

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

        # Twitter and orcid stuff
        info['apiRoot'].user.route('GET', (':id', 'orcid'), get_orcid)
        info['apiRoot'].user.route('POST', (':id', 'orcid'), set_orcid)
        info['apiRoot'].user.route('GET', (':id', 'twitter'), get_twitter)
        info['apiRoot'].user.route('POST', (':id', 'twitter'), set_twitter)

        # Launch a taskflow with a single endpoint
        info['apiRoot'].launch_taskflow = Resource()
        info['apiRoot'].launch_taskflow.route('POST', ('launch',),
                                              launch_taskflow_endpoint)
