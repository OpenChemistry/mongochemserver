from girder.api.describe import Description, autoDescribeRoute
from girder.api import access
from girder.api.rest import Resource
from girder.api.rest import getCurrentUser

from girder.constants import TokenScope

from .models.geometry import Geometry as GeometryModel


class Geometry(Resource):

    def __init__(self):
        super(Geometry, self).__init__()
        self.resourceName = 'geometry'
        self.route('POST', (), self.create)
        self.route('GET', (), self.find_geometries)

        self._model = GeometryModel()

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Create a geometry.')
        .param('moleculeId', 'The id of the parent molecule.')
        .jsonParam('cjson', 'The chemical json of the geometry.')
    )
    def create(self, params):
        self.requireParams(['moleculeId', 'cjson'], params)

        user = getCurrentUser()

        moleculeId = params['moleculeId']
        cjson = params['cjson']

        return self._model.create(moleculeId, cjson, 'user', user['_id'])

    @access.public
    @autoDescribeRoute(
        Description('Find geometries of a given molecule.')
        .param('moleculeId', 'The id of the parent molecule.')
    )
    def find_geometries(self, params):
        user = getCurrentUser()

        moleculeId = params['moleculeId']
        geometries = self._model.find_geometries(moleculeId)

        # Filter based upon access level.
        return [self._model.filter(x, user) for x in geometries]
