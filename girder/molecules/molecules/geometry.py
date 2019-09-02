from girder.api.describe import Description, autoDescribeRoute
from girder.api import access
from girder.api.rest import Resource
from girder.api.rest import RestException
from girder.api.rest import getCurrentUser

from girder.constants import AccessType
from girder.constants import TokenScope

from .models.geometry import Geometry as GeometryModel


class Geometry(Resource):

    def __init__(self):
        super(Geometry, self).__init__()
        self.resourceName = 'geometry'
        self.route('GET', (), self.find_geometries)
        self.route('POST', (), self.create)
        self.route('DELETE', (':id',), self.delete)

        self._model = GeometryModel()

    def _clean(self, doc):
        if 'access' in doc:
            del doc['access']

        return doc

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
        return [self._clean(self._model.filter(x, user)) for x in geometries]

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

        return self._clean(self._model.create(user, moleculeId, cjson, 'user',
                                              user['_id']))

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Delete a geometry.')
        .param('id', 'The id of the geometry to be deleted.')
        .errorResponse('Geometry not found.', 404)
    )
    def delete(self, id):
        user = self.getCurrentUser()
        geometry = GeometryModel().load(id, user=user, level=AccessType.WRITE)

        if not geometry:
            raise RestException('Geometry not found.', code=404)

        return GeometryModel().remove(geometry)
