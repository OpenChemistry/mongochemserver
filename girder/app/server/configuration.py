from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource, RestException
from girder.constants import AccessType, TokenScope
from girder.models.setting import Setting
from .constants import Features, Configuration as Conf

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
        config = {
            'notebooks': Setting().get(Features.NOTEBOOKS, True),
            'license': Setting().get(Conf.LICENSE),
            'privacy': Setting().get(Conf.PRIVACY),
            'headerLogoFileId': Setting().get(Conf.HEADER_LOGO_ID),
            'footerLogoFileId': Setting().get(Conf.FOOTER_LOGO_ID),
            'footerLogoUrl': Setting().get(Conf.FOOTER_LOGO_URL),
            'faviconFileId': Setting().get(Conf.FAVICON_ID)
        }
        return  {
            'features': {
                'notebooks': Setting().get(Features.NOTEBOOKS, True)
            },
            'configuration': {
                'license': Setting().get(Conf.LICENSE),
                'privacy': Setting().get(Conf.PRIVACY),
                'headerLogoFileId': Setting().get(Conf.HEADER_LOGO_ID),
                'footerLogoFileId': Setting().get(Conf.FOOTER_LOGO_ID),
                'footerLogoUrl': Setting().get(Conf.FOOTER_LOGO_URL),
                'faviconFileId': Setting().get(Conf.FAVICON_ID)
            }
        }
