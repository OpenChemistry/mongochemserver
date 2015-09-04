from jsonschema import validate, ValidationError

from girder.models.model_base import AccessControlledModel, ValidationException
from girder.constants import AccessType

class Calculation(AccessControlledModel):
    '''
    {
      'vibrationalModes': {
        'modes': []
        'frequencies': []
        'intensities': []
        'eigenVectors': {
            '<mode>': []
        },
        'frames': {
            '<mode>': [[3n]]
        }
      },
      'sdf': '...'
    }
    '''

    schema =  {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'required': ['vibrationalModes', 'sdf'],
        'properties': {
            "vibrationalModes": {
                'type': 'object',
                'required': ['modes', 'frequencies', 'intensities', 'eigenVectors'],
                'additionalProperties': False,
                'properties': {
                    'modes': {
                        'type': 'array',
                        'items': {
                            'type': 'integer'
                        }
                    },
                    'frequencies': {
                        'type': 'array',
                        'items': {
                            'type': 'number'
                        }
                    },
                    'intensities': {
                        'type': 'array',
                        'items': {
                            'type': 'number'
                        }
                    },
                    'eigenVectors': {
                        'type': 'object'
                    },
                    'frames': {
                        'type': 'object'
                    }
                }
            },
            'sdf': {
                'type': 'string'
            },
            'moleculeId': {
                'type': 'string'
            }
        }
    }

    def __init__(self):
        super(Calculation, self).__init__()

    def initialize(self):
        self.name = 'calculations'
        self.ensureIndices(['moleculeId'])

        self.exposeFields(level=AccessType.READ, fields=(
            '_id', 'moleculeId', 'sdf', 'vibrationalModes'))

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

        # Make sure arrays are same length
        modes = doc['vibrationalModes']['modes']
        frequencies = doc['vibrationalModes']['frequencies']
        intensities = doc['vibrationalModes']['intensities']

        if not len(modes) == len(frequencies) == len(intensities):
            raise ValidationException('Array length must match')

        return doc

    def create(self, user, sdf, vibrational_models, moleculeId=None):
        calc = {
            'vibrationalModes': vibrational_models,
            'sdf': sdf
        }

        if moleculeId:
            calc['moleculeId'] = moleculeId

        self.setUserAccess(calc, user=user, level=AccessType.ADMIN)
        return self.save(calc)


