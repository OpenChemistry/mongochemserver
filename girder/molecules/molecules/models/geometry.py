from bson.objectid import ObjectId

from girder.models.model_base import AccessControlledModel
from girder.constants import AccessType


class Geometry(AccessControlledModel):

    def __init__(self):
        super(Geometry, self).__init__()

    def initialize(self):
        self.name = 'geometry'
        self.ensureIndices(['moleculeId', 'cjson'])

        self.exposeFields(level=AccessType.READ, fields=(
            '_id', 'moleculeId', 'cjson', 'provenanceType', 'provenanceId'))

    def filter(self, geometry, user):
        geometry = super(Geometry, self).filter(doc=geometry, user=user)

        del geometry['_accessLevel']
        del geometry['_modelType']

        return geometry

    def validate(self, doc):
        # If we have a moleculeId ensure it is valid.
        if 'moleculeId' in doc:
            mol = self.model('molecule', 'molecules').load(doc['moleculeId'],
                                                           force=True)
            doc['moleculeId'] = mol['_id']

        return doc

    def create(self, user, moleculeId, cjson, provenanceType=None,
               provenanceId=None, public=False):
        geometry = {
            'moleculeId': moleculeId,
            'cjson': cjson
        }

        if provenanceType is not None:
            geometry['provenanceType'] = provenanceType

        if provenanceId is not None:
            geometry['provenanceId'] = provenanceId

        self.setUserAccess(geometry, user=user, level=AccessType.ADMIN)
        if public:
            self.setPublic(geometry, True)

        return self.save(geometry)

    def find_geometries(self, moleculeId):
        query = {
            'moleculeId': ObjectId(moleculeId)
        }

        return self.find(query)
