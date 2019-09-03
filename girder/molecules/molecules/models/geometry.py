from bson.objectid import ObjectId

from girder.models.model_base import AccessControlledModel
from girder.constants import AccessType

from .molecule import Molecule as MoleculeModel


class Geometry(AccessControlledModel):

    def __init__(self):
        super(Geometry, self).__init__()

    def initialize(self):
        self.name = 'geometry'
        self.ensureIndex('moleculeId')

        self.exposeFields(level=AccessType.READ, fields=(
            '_id', 'moleculeId', 'cjson', 'provenanceType', 'provenanceId'))

    def validate(self, doc):
        # If we have a moleculeId ensure it is valid.
        if 'moleculeId' in doc:
            mol = MoleculeModel().load(doc['moleculeId'], force=True)
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

    def find_geometries(self, moleculeId, user=None):
        query = {
            'moleculeId': ObjectId(moleculeId)
        }

        return self.findWithPermissions(query, user=user)
