from jsonschema import validate, ValidationError

from girder.models.model_base import AccessControlledModel, ValidationException
from girder.constants import AccessType

class Experimental(AccessControlledModel):
    '''
    {
        "spectrumType": "Infrared",
        "experimentalTechnique": "InfraRed Multiphoton Dissociation - IRMPD",
        "id": "[UO2(TMGA-R=CH2)3]2+",
        "molecularFormula" : "C27H54N6O8U1",
        "measuredSpectrum": {
          "frequencies": {
            "units": "cm-1"
            "values": []
          },
          "intensities": {
            "units": "arbitrary units",
            "values": []
          }
        }
    }
    '''

    schema =  {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'required': ['spectrumType', 'experimentalTechnique', 'id',
                     'molecularFormula', 'measuredSpectrum'],
        'properties': {
            'spectrumType': {
                'type': 'string'
            },
            'experimentalTechnique': {
                'type': 'string'
            },
            'id': {
                'type': 'string'
            },
            'molecularFormula': {
                'type': 'string'
            },
            'measuredSpectrum': {
                'type': 'object',
                'required': ['frequencies', 'intensities'],
                'properties': {
                    'frequencies': {
                        'type': 'object',
                        'required': ['units', 'values'],
                        'properties': {
                            'units': {
                                'type': 'string'
                            },
                            'values': {
                                'type': 'array',
                                'items': {
                                    'type': 'number'
                                }
                            }

                        }
                    },
                    'intensities': {
                        'type': 'object',
                        'required': ['units', 'values'],
                        'properties': {
                            'units': {
                                'type': 'string'
                            },
                            'values': {
                                'type': 'array',
                                'items': {
                                    'type': 'number'
                                }
                            }

                        }
                    }
                }
            }
        }
    }

    def __init__(self):
        super(Experimental, self).__init__()

    def initialize(self):
        self.name = 'experimental'
        self.ensureIndices(['molecularFormula'])

        self.exposeFields(level=AccessType.READ, fields=(
            'spectrumType', 'experimentalTechnique', 'id', '_id',
                     'molecularFormula', 'measuredSpectrum', 'name'))

    def filter(self, calc, user):
        calc = super(Experimental, self).filter(doc=calc, user=user)

        del calc['_accessLevel']
        del calc['_modelType']

        return calc

    def validate(self, doc):
        try:
            validate(doc, Experimental.schema)

        except ValidationError as ex:
            raise ValidationException(ex.message)

        # Make sure arrays are same length
        frequencies = doc['measuredSpectrum']['frequencies']
        intensities = doc['measuredSpectrum']['intensities']

        if len(frequencies) != len(intensities):
            raise ValidationException('Array length must match')

        return doc

    def create(self, facility_used, spectrum_type, experimental_technique, id,
               molecular_formula, measured_spectrum):
        experiment = {
             'facilityUsed': facility_used,
             'spectrumType': spectrum_type,
             'experimentalTechnique': experimental_technique,
             'id': id,
             'molecularFormula' : molecular_formula,
             'measuredSpectrum' : measured_spectrum,
             'name': '%s (%s)' % (experimental_technique, spectrum_type)
        }

        # For now set as public
        self.setPublic(experiment, True)

        return self.save(experiment)
