import cherrypy
import functools
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

from . import avogadro

class Calculation(Resource):
    output_formats = ['cml', 'xyz', 'inchikey', 'sdf']
    input_formats = ['cml', 'xyz', 'pdb']

    def __init__(self):
        super(Calculation, self).__init__()
        self.resourceName = 'calculations'
        self.route('POST', (), self.create_calc)
        self.route('GET', (), self.find_calc)
        self.route('GET', ('types',), self.find_calc_types)
        self.route('GET', (':id', 'vibrationalmodes'),
            self.get_calc_vibrational_modes)
        self.route('GET', (':id', 'vibrationalmodes', ':mode'),
            self.get_calc_vibrational_mode)
        self.route('GET', (':id', 'sdf'),
            self.get_calc_sdf)
        self.route('GET', (':id', 'cjson'),
            self.get_calc_cjson)
        self.route('GET', (':id', 'cube', ':mo'),
            self.get_calc_cube)

        self._model = self.model('calculation', 'molecules')
        self._cube_model = self.model('cubecache', 'molecules')

    @access.public
    def get_calc_vibrational_modes(self, id, params):

        fields = ['cjson.modes', 'cjson.intensities',
                 'cjson.frequencies', 'access']

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

        fields = ['cjson.modes', 'access']
        calc =  self._model.load(id, fields=fields, user=getCurrentUser(),
                                 level=AccessType.READ)

        vibrational_modes = calc['cjson.vibrations']
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
            'cjson.vibrations.frequencies': {
                '$slice': [index, 1]
            },
            'cjson.vibrations.intensities': {
                '$slice': [index, 1]
            },
            'cjson.vibrations.eigenVectors': {
                '$slice': [index, 1]
            }
        }

        mode = self._model.findOne(query, fields=projection)

        return mode


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

    @access.public
    def get_calc_cube(self, id, mo, params):
        try:
            mo = int(mo)
        except ValueError:
            raise ValidationException('mo number be an integer', 'mode')

        cached = self._cube_model.find_mo(id, mo)

        # If we have a cached cube file use that.
        if cached:
            return cached['cjson']

        fields = ['cjson', 'access', 'fileId']

        # Ignoring access control on file/data for now, all public.
        calc =  self._model.load(id, fields=fields, force=True)

        file_id = calc['fileId']
        file = self.model('file').load(file_id, force=True)
        parts = file['name'].split('.')
        input_format = parts[-1]
        name = '.'.join(parts[:-1])

        contents = functools.reduce(lambda x, y: x + y, self.model('file').download(file, headers=False)())
        data_str = contents.decode()

        # This is where the cube gets calculated, should be cached in future.
        cjson = avogadro.calculate_mo(data_str, mo)

        # Remove the vibrational mode data from the cube - big, not needed here.
        if 'vibrations' in cjson:
            del cjson['vibrations']

        # Cache this cube for the next time, they can take a while to generate.
        self._cube_model.create(id, mo, cjson)

        return cjson

    get_calc_cube.description = (
        Description('Get the cube for the supplied MO of the calculation in CJSON format')
        .param(
            'id',
            'The id of the calculation to return the structure for.',
            dataType='string', required=True, paramType='path')
        .param(
            'mo',
            'The molecular orbital to get the cube for.',
            dataType='string', required=True, paramType='path'))

    @access.user
    def create_calc(self, params):
        body = getBodyJson()
        self.requireParams(['cjson'],  body)
        user = getCurrentUser()

        cjson = body['cjson']
        props = body.get('properties', {})
        moleculeId = body.get('moleculeId', None)

        calc = self._model.create_cjson(user, cjson, props, moleculeId)

        cherrypy.response.status = 201
        cherrypy.response.headers['Location'] \
            = '/molecules/%s/calc/%s' % (id, str(calc['_id']))

        return self._model.filter(calc, user)

    # Try and reuse schema for documentation, this only partially works!
    calc_schema = Calculation.schema.copy()
    calc_schema['id'] = 'CalculationData'
    addModel('Calculation', 'CalculationData', calc_schema)

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
        if 'calculationType' in params:
            query['properties.calculationTypes'] = params['calculationType']

        limit = params.get('limit', 50)

        fields = ['cjson.vibrations.modes', 'cjson.vibrations.intensities',
                 'cjson.vibrations.frequencies', 'properties', 'fileId', 'access', 'public']
        calcs = self._model.find(query, fields=fields)
        calcs = self._model.filterResultsByPermission(calcs, user,
            AccessType.READ, limit=int(limit))

        return [self._model.filter(x, user) for x in calcs]

    find_calc.description = (
        Description('Search for particular calculation')
        .param(
            'moleculeId',
            'The moleculeId the calculations should be associated with',
            dataType='string', paramType='query', required=False)
        .param(
            'calculationType',
            'The type of calculations being searched for',
            dataType='string', paramType='query', required=False)
        .param(
            'limit',
            'The max number of calculations to return',
             dataType='integer', paramType='query', default=50, required=False))

    @access.public
    def find_calc_types(self, params):
        fields = ['access', 'properties.calculationTypes']

        query = { }
        if 'moleculeId' in params:
            query['moleculeId'] = ObjectId(params['moleculeId'])

        calcs = self._model.find(query, fields=fields)

        allTypes = []
        for types in calcs:
            calc_types = parse('properties.calculationTypes').find(types)
            if calc_types:
                calc_types = calc_types[0].value
                allTypes.extend(calc_types)

        typeSet = set(allTypes)

        return list(typeSet)

    find_calc_types.description = (
        Description('Get the calculation types available for the molecule')
        .param(
            'moleculeId',
            'The id of the molecule we are finding types for.',
            dataType='string', required=True, paramType='query'))

