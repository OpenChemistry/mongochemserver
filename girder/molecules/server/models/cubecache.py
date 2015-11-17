from jsonschema import validate, ValidationError
from bson.objectid import ObjectId

from girder.models.model_base import AccessControlledModel, ValidationException
from girder.constants import AccessType

class Cubecache(AccessControlledModel):

    def __init__(self):
        super(Cubecache, self).__init__()

    def initialize(self):
        self.name = 'cubecache'
        self.ensureIndices(['calculationId', 'mo'])

        self.exposeFields(level=AccessType.READ, fields=(
            '_id', 'calculationId', 'mo', 'cjson'))

    def filter(self, calc, user):
        calc = super(Calculation, self).filter(doc=calc, user=user)

        del calc['_accessLevel']
        del calc['_modelType']

        return calc

    def validate(self, doc):
        # If we have a calculationId check it is valid.
        if 'calculationId' in doc:
            calc = self.model('calculation', 'molecules').load(doc['calculationId'],
                                                               force=True)
            doc['calculationId'] = calc['_id']

        return doc

    def create(self, calcId, mo, cjson):
        cache = {
            'calculationId': calcId,
            'mo': mo,
            'cjson': cjson
        }

        # For now set as public
        self.setPublic(cache, True)

        return self.save(cache)

    def find_mo(self, calcId, mo):
        query = {
            'calculationId': ObjectId(calcId),
            'mo': mo
        }

        cache = self.findOne(query)

        return cache
