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
      'cjson': '...'
    }
    '''

    schema =  {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'required': ['cjson'],
        'properties': {
            "vibrationalModes": {
                'type': 'object',
                'required': ['modes', 'frequencies', 'intensities', 'eigenVectors'],
                'additionalProperties': True,
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
                        'type': 'array',
                        'items': {
                            '$ref': '#/definitions/eigenVector'
                        }
                    }
                }
            }
        },
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
        self.ensureIndices(['moleculeId'])

        self.exposeFields(level=AccessType.READ, fields=(
            '_id', 'moleculeId', 'fileId', 'properties'))

    def filter(self, calc, user):
        calc = super(Calculation, self).filter(doc=calc, user=user)

        del calc['_accessLevel']
        del calc['_modelType']

        return calc

    def validate(self, doc):
        if 'vibrationalModes' in doc:
            try:
                validate(doc, Calculation.schema)

            except ValidationError as ex:
                raise ValidationException(ex.message)

            # Make sure arrays are same length
            modes = doc['vibrationalModes']['modes']
            frequencies = doc['vibrationalModes']['frequencies']
            intensities = doc['vibrationalModes']['intensities']
            eigenVectors = doc['vibrationalModes']['eigenVectors']

            if not len(modes) == len(frequencies) == len(intensities) \
                == len(eigenVectors):
                raise ValidationException('Array length must match')

        # If we have a moleculeId check it valid
        if 'moleculeId' in doc:
            mol = self.model('molecule', 'molecules').load(doc['moleculeId'],
                                                           force=True)
            doc['moleculeId'] = mol['_id']

        return doc

    def create(self, user, sdf, vibrational_models, moleculeId=None):
        calc = {
            'vibrationalModes': vibrational_models,
            'sdf': sdf
        }

        if moleculeId:
            calc['moleculeId'] = moleculeId

        self.setUserAccess(calc, user=user, level=AccessType.ADMIN)
        # For now set as public
        self.setPublic(calc, True)

        return self.save(calc)

    def create_cjson(self, user, cjson, props, moleculeId = None, fileId = None):
        calc = {
            'cjson': cjson,
            'properties': props
        }
        if moleculeId:
            calc['moleculeId'] = moleculeId
        if fileId:
            calc['fileId'] = fileId

        self.setUserAccess(calc, user=user, level=AccessType.ADMIN)
        # For now set as public
        self.setPublic(calc, True)

        return self.save(calc)
