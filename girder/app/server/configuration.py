from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource, RestException
from girder.constants import AccessType, TokenScope
from girder.models.setting import Setting
from .constants import Features, Branding

class Configuration(Resource):

    def __init__(self):
        super(Configuration, self).__init__()
        self.resourceName = 'configuration'
        self.route('GET', (), self.get)

    @access.public
    @autoDescribeRoute(
        Description('Get the deployment configuration.')
    )
    def get(self):
        return  {
            'features': {
                'notebooks': Setting().get(Features.NOTEBOOKS, True)
            },
            'branding': {
                'license': Setting().get(Branding.LICENSE),
                'privacy': Setting().get(Branding.PRIVACY),
                'headerLogoFileId': Setting().get(Branding.HEADER_LOGO_ID),
                'footerLogoFileId': Setting().get(Branding.FOOTER_LOGO_ID),
                'footerLogoUrl': Setting().get(Branding.FOOTER_LOGO_URL),
                'faviconFileId': Setting().get(Branding.FAVICON_ID)
            }
        }
