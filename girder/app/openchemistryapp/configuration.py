from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource, RestException
from girder.constants import AccessType, TokenScope
from girder.models.setting import Setting
from .constants import Features

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
        return {
            'features': {
                'notebooks': Setting().get(Features.NOTEBOOKS, True)
            }
        }

