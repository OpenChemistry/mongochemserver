import cherrypy
from jsonpath_rw import parse

from girder.api.describe import Description
from girder.api.docs import addModel
from girder.api import access
from girder.api.rest import Resource
from girder.api.rest import RestException, getBodyJson, getCurrentUser, \
    loadmodel
from girder.models.model_base import ModelImporter
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

        self._model = self.model('calculation', 'molecules')

    @access.user
    @loadmodel(model='calculation', plugin='molecules',
               level=AccessType.READ)
    def get_calc_vibrational_modes(self, calculation, params):
        return calculation['vibrationalModes']

    get_calc_vibrational_modes.description = (
        Description('Get the vibrational modes associated with a calculation')
        .param(
            'id',
            'The id of the calculation to get the modes from.',
            dataType='string', required=True, paramType='path'))

    @access.user
    @loadmodel(model='calculation', plugin='molecules', level=AccessType.READ)
    def get_calc_vibrational_mode(self, calculation, mode, params):
        frames = calculation.get('vibrationalModes', {}).get('frames', {})

        if not frames or mode not in frames:
            raise RestException('No such vibrational mode', 400)

        return frames[mode]

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

    @access.user
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

    @access.user
    def find_calc(self, params):
        user = getCurrentUser()

        query = { }

        if 'moleculeId' in params:
            query['moleculeId'] = params['moleculeId']

        limit = params.get('limit', 50)

        calcs = self._model.find(query)
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