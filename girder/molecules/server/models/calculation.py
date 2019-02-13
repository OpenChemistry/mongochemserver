from jsonschema import validate, ValidationError

from girder.models.model_base import AccessControlledModel, ValidationException
from girder.constants import AccessType

import openchemistry as oc

class Calculation(AccessControlledModel):
    '''
    {
        'frames': {
            '<mode>': [[3n]]
        }
      },
      'cjson': '...'
    }
    '''

    schema =  {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'required': ['cjson'],
        'definitions': {
            'frame': {
                'type': 'array',
                'items': {
                    'type': 'number'
                }
            },
            'modeFrame': {
                'type': 'array',
                'items': {
                    '$ref': '#/definitions/frame'
                }
            },
            'eigenVector': {
                'type': 'array',
                'items': {
                    'type': 'number'
                }
            }
        }
    }

    def __init__(self):
        super(Calculation, self).__init__()

    def initialize(self):
        self.name = 'calculations'
        self.ensureIndices([
            'moleculeId', 'calculationType', 'properties.functional',
            'properties.theory', 'properties.basisSet.name', 'properties.pending',
            'properties.code', 'properties.theoryPriority'
        ])

        self.exposeFields(level=AccessType.READ, fields=(
            '_id', 'moleculeId', 'fileId', 'properties', 'notebooks'))

    def filter(self, calc, user):
        calc = super(Calculation, self).filter(doc=calc, user=user)

        del calc['_accessLevel']
        del calc['_modelType']

        return calc

    def validate(self, doc):
        try:
            validate(doc, Calculation.schema)

        except ValidationError as ex:
            raise ValidationException(ex.message)

        # If we have a moleculeId check it valid
        if 'moleculeId' in doc:
            mol = self.model('molecule', 'molecules').load(doc['moleculeId'],
                                                           force=True)
            doc['moleculeId'] = mol['_id']

        return doc

    def create_cjson(self, user, cjson, props, molecule_id= None,
                     container_name=None, input_parameters=None,
                     file_id = None, public=False, notebooks=None):
        if notebooks is None:
            notebooks = []

        calc = {
            'cjson': cjson,
            'properties': props,
            'notebooks': notebooks
        }
        if molecule_id:
            calc['moleculeId'] = molecule_id
        if file_id:
            calc['fileId'] = file_id
        if container_name:
            calc['containerName'] = container_name
        if input_parameters is not None:
            calc['inputParameters'] = input_parameters
            calc['inputParametersHash'] = oc.hash_object(input_parameters)

        self.setUserAccess(calc, user=user, level=AccessType.ADMIN)
        if public:
            self.setPublic(calc, True)

        return self.save(calc)

    def add_notebooks(self, calc, notebooks):
        query = {
            '_id': calc['_id']
        }

        update = {
            '$addToSet': {
                'notebooks': {
                    '$each': notebooks
                }
            }
        }
        super(Calculation, self).update(query, update)
