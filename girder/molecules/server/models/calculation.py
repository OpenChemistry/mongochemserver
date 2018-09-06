from jsonschema import validate, ValidationError
from jsonpath_rw import parse

from girder.models.model_base import AccessControlledModel, ValidationException
from girder.constants import AccessType

from .. import constants

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
            'theoryPriority'
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

    def create_cjson(self, user, cjson, props, moleculeId = None, fileId = None,
                     public=False, notebooks=[]):
        calc = {
            'cjson': cjson,
            'notebooks': notebooks
        }
        if moleculeId:
            calc['moleculeId'] = moleculeId
        if fileId:
            calc['fileId'] = fileId

        if 'vibrations' in cjson or 'basisSet' in cjson:
            # The calculation is no longer pending
            if 'pending' in props:
                del props['pending']

            # Use basisSet from cjson if we don't already have one.
            if 'basisSet' in cjson and 'basisSet' not in props:
                props['basisSet'] = cjson['basisSet']

            # Use functional from cjson properties if we don't already have
            # one.
            functional = parse('properties.functional').find(cjson)
            if functional and 'functional' not in props:
                props['functional'] = functional[0].value

            # Add theory priority to 'sort' calculations
            theory = props.get('theory')
            if theory in constants.theory_priority:
                priority = constants.theory_priority[theory]
                props['theoryPriority'] = priority

        calc['properties'] = props

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
