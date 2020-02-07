from bson.objectid import ObjectId

from girder.models.model_base import AccessControlledModel
from girder.constants import AccessType

from molecules.models.molecule import Molecule as MoleculeModel
from molecules.utilities.get_cjson_energy import get_cjson_energy
from molecules.utilities.pagination import parse_pagination_params
from molecules.utilities.pagination import search_results_dict
from molecules.utilities.whitelist_cjson import whitelist_cjson

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
               provenanceId=None, public=True):

        # We will whitelist the cjson to only include the geometry parts
        geometry = {
            'moleculeId': moleculeId,
            'cjson': whitelist_cjson(cjson),
            'creatorId': user['_id']
        }

        if provenanceType is not None:
            geometry['provenanceType'] = provenanceType

        if provenanceId is not None:
            geometry['provenanceId'] = provenanceId

        # If the cjson has an energy, set it
        energy = get_cjson_energy(cjson)
        if energy is not None:
            geometry['energy'] = energy

        self.setUserAccess(geometry, user=user, level=AccessType.ADMIN)
        if public:
            self.setPublic(geometry, True)

        return self.save(geometry)

    def find_geometries(self, moleculeId, user, paging_params):

        limit, offset, sort = parse_pagination_params(paging_params)

        query = {
            'moleculeId': ObjectId(moleculeId)
        }

        fields = [
          'creatorId',
          'moleculeId',
          'provenanceId',
          'provenanceType',
          'energy'
        ]

        cursor = self.findWithPermissions(query, user=user, fields=fields,
                                          limit=limit, offset=offset,
                                          sort=sort)

        num_matches = cursor.collection.count_documents(query)

        geometries = [x for x in cursor]
        return search_results_dict(geometries, num_matches, limit, offset, sort)
