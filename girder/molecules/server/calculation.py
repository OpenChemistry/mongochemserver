import cherrypy
from jsonpath_rw import parse
from bson.objectid import ObjectId

from girder.api.describe import Description
from girder.api.docs import addModel
from girder.api import access
from girder.api.rest import Resource
from girder.api.rest import RestException, getBodyJson, getCurrentUser, \
    loadmodel
from girder.models.model_base import ModelImporter, ValidationException
from girder.constants import AccessType

from girder.plugins.molecules.models.calculation import Calculation


class Calculation(Resource):
    output_formats = ['cml', 'xyz', 'inchikey', 'sdf']
    input_formats = ['cml', 'xyz', 'pdb']

    def __init__(self):
        self.resourceName = 'calculations'
        self.route('POST', (), self.create_calc)
        self.route('GET', (), self.find_calc)
        self.route('GET', (':id', 'vibrationalmodes'),
            self.get_calc_vibrational_modes)
        self.route('GET', (':id', 'vibrationalmodes', ':mode'),
            self.get_calc_vibrational_mode)
        self.route('GET', (':id', 'sdf'),
            self.get_calc_sdf)
        self.route('GET', (':id', 'cjson'),
            self.get_calc_cjson)

        self._model = self.model('calculation', 'molecules')

    @access.public
    def get_calc_vibrational_modes(self, id, params):

        fields = ['vibrationalModes.modes', 'vibrationalModes.intensities',
                 'vibrationalModes.frequencies', 'access']

        calc =  self._model.load(id, fields=fields, user=getCurrentUser(),
                                 level=AccessType.READ)

        del calc['access']

        return calc

    get_calc_vibrational_modes.description = (
        Description('Get the vibrational modes associated with a calculation')
        .param(
            'id',
            'The id of the calculation to get the modes from.',
            dataType='string', required=True, paramType='path'))

    @access.public
    def get_calc_vibrational_mode(self, id, mode, params):

        try:
            mode = int(mode)
        except ValueError:
            raise ValidationException('mode number be an integer', 'mode')

        fields = ['vibrationalModes.modes', 'access']
        calc =  self._model.load(id, fields=fields, user=getCurrentUser(),
                                 level=AccessType.READ)

        vibrational_modes = calc['vibrationalModes']
        #frames = vibrational_modes.get('modeFrames')
        modes = vibrational_modes.get('modes', [])

        index = modes.index(mode)
        if index < 0:
            raise RestException('No such vibrational mode', 400)

        # Now select the modeFrames directly this seems to be more efficient
        # than iterating in Python
        query = {
            '_id': calc['_id']
        }

        projection = {
            'vibrationalModes.modeFrames': {
                '$slice': [index, 1]
            },
            'vibrationalModes.frequencies': {
                '$slice': [index, 1]
            },
            'vibrationalModes.intensities': {
                '$slice': [index, 1]
            }
        }

        mode_frames = self._model.findOne(query, fields=projection)

        return mode_frames['vibrationalModes']['modeFrames'][0]


    get_calc_vibrational_mode.description = (
        Description('Get a vibrational mode associated with a calculation')
        .param(
            'id',
            'The id of the calculation that the mode is associated with.',
            dataType='string', required=True, paramType='path')
        .param(
            'mode',
            'The index of the vibrational model to get.',
            dataType='string', required=True, paramType='path'))

    @access.public
    @loadmodel(model='calculation', plugin='molecules', level=AccessType.READ)
    def get_calc_sdf(self, calculation, params):

        def stream():
            cherrypy.response.headers['Content-Type'] = 'chemical/x-mdl-sdfile'
            yield calculation['sdf']

        return stream

    get_calc_sdf.description = (
        Description('Get the molecular structure of a give calculation in SDF format')
        .param(
            'id',
            'The id of the calculation to return the structure for.',
            dataType='string', required=True, paramType='path'))

    @access.public
    @loadmodel(model='calculation', plugin='molecules', level=AccessType.READ)
    def get_calc_cjson(self, calculation, params):
        return calculation['cjson']

    get_calc_cjson.description = (
        Description('Get the molecular structure of a give calculation in CJSON format')
        .param(
            'id',
            'The id of the calculation to return the structure for.',
            dataType='string', required=True, paramType='path'))

    @access.user
    def create_calc(self, params):
        body = getBodyJson()
        self.requireParams(['sdf', 'vibrationalModes'],  body)
        user = getCurrentUser()

        sdf = body['sdf']
        vibrational_modes = body['vibrationalModes']
        moleculeId = body.get('moleculeId', None)

        calc = self._model.create(user, sdf, vibrational_modes, moleculeId)

        cherrypy.response.status = 201
        cherrypy.response.headers['Location'] \
            = '/molecules/%s/calc/%s' % (id, str(calc['_id']))

        return self._model.filter(calc, user)

    # Try and reuse schema for documentation, this only partially works!
    calc_schema = Calculation.schema.copy()
    calc_schema['id'] = 'CalculationData'
    addModel('CalculationData', calc_schema)

    create_calc.description = (
        Description('Get the molecular structure of a give calculation in SDF format')
        .param(
            'body',
            'The calculation data', dataType='CalculationData', required=True,
            paramType='body'))

    @access.public
    def find_calc(self, params):
        user = getCurrentUser()

        query = { }

        if 'moleculeId' in params:
            query['moleculeId'] = ObjectId(params['moleculeId'])

        limit = params.get('limit', 50)

        fields = ['vibrationalModes.modes', 'vibrationalModes.intensities',
                 'vibrationalModes.frequencies', 'access', 'public']
        calcs = self._model.find(query, fields=fields)
        calcs = self._model.filterResultsByPermission(calcs, user,
            AccessType.READ, limit=int(limit))

        return [self._model.filter(x, user) for x in calcs]

    find_calc.description = (
        Description('Search for particular calculation')
        .param(
            'moleculeId',
            'The moleculeId the calcualtions should be associated with',
            dataType='string', paramType='query', required=False)
        .param(
            'limit',
            'The max number of calculations to return',
             dataType='integer', paramType='query', default=50, required=False))