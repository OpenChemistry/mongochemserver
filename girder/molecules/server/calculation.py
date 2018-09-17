import cherrypy
import functools
from jsonpath_rw import parse
from bson.objectid import ObjectId
import json

from girder.api.describe import Description, autoDescribeRoute
from girder.api.docs import addModel
from girder.api import access
from girder.api.rest import Resource
from girder.api.rest import RestException, getBodyJson, getCurrentUser, \
    loadmodel
from girder.models.model_base import ModelImporter, ValidationException
from girder.models.file import File
from girder.constants import AccessType, TokenScope
from girder.utility import toBool
from girder.plugins.molecules.models.calculation import Calculation as CalculationModel
from girder.plugins.molecules.utilities.molecules import create_molecule

from . import avogadro
from . import constants
from .molecule import Molecule
import pymongo


class Calculation(Resource):
    output_formats = ['cml', 'xyz', 'inchikey', 'sdf']
    input_formats = ['cml', 'xyz', 'pdb']

    def __init__(self):
        super(Calculation, self).__init__()
        self.resourceName = 'calculations'
        self.route('POST', (), self.create_calc)
        self.route('PUT', (':id', ), self.ingest_calc)
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
        self.route('GET', (':id', 'xyz'),
            self.get_calc_xyz)
        self.route('GET', (':id', 'cube', ':mo'),
            self.get_calc_cube)
        self.route('GET', (':id',),
            self.find_id)
        self.route('PUT', (':id', 'properties'),
            self.update_properties)
        self.route('PATCH', (':id', 'notebooks'), self.add_notebooks)


        self._model = self.model('calculation', 'molecules')
        self._cube_model = self.model('cubecache', 'molecules')

    @access.public
    def get_calc_vibrational_modes(self, id, params):

        fields = ['cjson..vibrations.modes', 'cjson.vibrations.intensities',
                 'cjson.vibrations.frequencies', 'access']

        calc =  self._model.load(id, fields=fields, user=getCurrentUser(),
                                 level=AccessType.READ)

        del calc['access']

        return calc['cjson']['vibrations']

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

        fields = ['cjson.vibrations.modes', 'access']
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
    @loadmodel(model='calculation', plugin='molecules', level=AccessType.READ)
    def get_calc_xyz(self, calculation, params):
        data = json.dumps(calculation['cjson'])
        data = avogadro.convert_str(data, 'cjson', 'xyz')

        def stream():
            cherrypy.response.headers['Content-Type'] = Molecule.mime_types['xyz']
            yield data

        return stream

    get_calc_xyz.description = (
        Description('Get the molecular structure of a give calculation in XYZ format')
        .param(
            'id',
            'The id of the calculation to return the structure for.',
            dataType='string', required=True, paramType='path'))

    @access.public
    def get_calc_cube(self, id, mo, params):
        try:
            mo = int(mo)
        except ValueError:

            # Check for homo lumo
            mo = mo.lower()
            if mo in ['homo', 'lumo']:
                cal = self._model.load(id, force=True)
                electron_count = parse('cjson.basisSet.electronCount').find(cal)
                if electron_count:
                    electron_count = electron_count[0].value
                else:
                    # Look here as well.
                    electron_count = parse('properties.electronCount').find(cal)
                    if electron_count:
                        electron_count = electron_count[0].value
                    else:
                        raise RestException('Unable to access electronCount', 400)
                # The index of the first orbital is 0, so homo needs to be
                # electron_count // 2 - 1
                if mo == 'homo':
                    mo = int(electron_count / 2) - 1
                elif mo == 'lumo':
                    mo = int(electron_count / 2)
            else:
                raise ValidationException('mo number be an integer or \'homo\'/\'lumo\'', 'mode')


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

        with self.model('file').open(file) as fp:
            data_str = fp.read().decode()

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
        if 'cjson' not in  body and 'fileId' not in body:
            raise RestException('Either cjson or fileId is required.')

        user = getCurrentUser()

        cjson = body.get('cjson')
        props = body.get('properties', {})
        molecule_id = body.get('moleculeId', None)
        public = body.get('public', False)
        notebooks = body.get('notebooks', [])
        file_id = None

        if 'fileId' in body:
            file = File().load(body['fileId'], user=getCurrentUser())
            file_id = file['_id']
            with File().open(file) as f:
                calc_data = f.read().decode()
                cjson = avogadro.convert_str(calc_data, 'json', 'cjson')
                cjson = json.loads(cjson)

            if 'vibrations' in cjson or 'basisSet' in cjson:

                props = self._extract_calculation_properties(cjson, json.loads(calc_data))

        if molecule_id is None:
            mol = create_molecule(json.dumps(cjson), 'cjson', user, public)
            molecule_id = mol['_id']

        calc = CalculationModel().create_cjson(user, cjson, props, molecule_id, file_id=file_id,
                                               notebooks=notebooks, public=public)

        cherrypy.response.status = 201
        cherrypy.response.headers['Location'] \
            = '/calculations/%s' % (str(calc['_id']))

        return CalculationModel().filter(calc, user)

    # Try and reuse schema for documentation, this only partially works!
    calc_schema = CalculationModel.schema.copy()
    calc_schema['id'] = 'CalculationData'
    addModel('Calculation', 'CalculationData', calc_schema)

    create_calc.description = (
        Description('Get the molecular structure of a give calculation in SDF format')
        .param(
            'body',
            'The calculation data', dataType='CalculationData', required=True,
            paramType='body'))

    def _extract_calculation_properties(self, cjson, calculation_data):
        calc_props = avogadro.calculation_properties(calculation_data)

        # Use basisSet from cjson if we don't already have one.
        if 'basisSet' in cjson and 'basisSet' not in calc_props:
            calc_props['basisSet'] = cjson['basisSet']

        # Use functional from cjson properties if we don't already have
        # one.
        functional = parse('properties.functional').find(cjson)
        if functional and 'functional' not in calc_props:
            calc_props['functional'] = functional[0].value

        # Add theory priority to 'sort' calculations
        theory = calc_props.get('theory')
        functional = calc_props.get('functional')
        if theory in constants.theory_priority:
            priority = constants.theory_priority[theory]
            calc_props['theoryPriority'] = priority

        return calc_props

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Update pending calculation with results.')
        .modelParam('id', 'The calculation id',
            model=CalculationModel, destName='calculation',
            level=AccessType.WRITE, paramType='path')
        .jsonParam('body', 'The calculation details', required=True, paramType='body')
    )
    def ingest_calc(self, calculation, body):
        self.requireParams(['fileId'], body)

        file = File().load(body['fileId'], user=getCurrentUser())
        with File().open(file) as f:
            calc_data = f.read().decode()
            cjson = avogadro.convert_str(calc_data, 'json', 'cjson')
            cjson = json.loads(cjson)

        if 'vibrations' in cjson or 'basisSet' in cjson:
            calc_props = calculation['properties']
            # The calculation is no longer psending
            if 'pending' in calc_props:
                del calc_props['pending']

            new_props = self._extract_calculation_properties(cjson, json.loads(calc_data))
            new_props.update(calc_props)
            calc_props = new_props

            calculation['properties'] = calc_props
            calculation['cjson'] = cjson
            calculation['fileId'] = file['_id']

            return CalculationModel().save(calculation)

    @access.public
    def find_calc(self, params):
        user = getCurrentUser()

        query = { }

        if 'moleculeId' in params:
            query['moleculeId'] = ObjectId(params['moleculeId'])
        if 'calculationType' in params:
            calculation_type = params['calculationType']
            if not isinstance(calculation_type, list):
                calculation_type = [calculation_type]

            query['properties.calculationTypes'] = {
                '$all': calculation_type
            }

        if 'functional' in params:
            query['properties.functional'] = params.get('functional').lower()

        if 'theory' in params:
            query['properties.theory'] = params.get('theory').lower()

        if 'basis' in params:
            query['properties.basisSet.name'] = params.get('basis').lower()

        if 'pending' in params:
            pending = toBool(params['pending'])
            query['properties.pending'] = pending
            # The absence of the field mean the calculation is not pending ...
            if not pending:
                query['properties.pending'] = {
                    '$ne': True
                }

        limit = params.get('limit', 50)

        fields = ['cjson.vibrations.modes', 'cjson.vibrations.intensities',
                 'cjson.vibrations.frequencies', 'properties', 'fileId', 'access', 'public']
        sort = None
        sort_by_theory = toBool(params.get('sortByTheory', False))
        if sort_by_theory:
            sort = [('properties.theoryPriority', pymongo.DESCENDING)]
            # Exclude calculations that don't have a theoryPriority,
            # otherwise they will appear first in the list.
            query['properties.theoryPriority'] = { '$exists': True }

        calcs = self._model.find(query, fields=fields, sort=sort)
        calcs = self._model.filterResultsByPermission(calcs, user,
            AccessType.READ, limit=int(limit))
        calcs = [self._model.filter(x, user) for x in calcs]

        not_sortable = []
        if sort_by_theory and len(calcs) < int(limit):
            # Now select any calculations without theoryPriority
            query['properties.theoryPriority'] = { '$exists': False }
            not_sortable = self._model.find(query, fields=fields)
            not_sortable = self._model.filterResultsByPermission(not_sortable, user,
            AccessType.READ, limit=int(limit) - len(calcs))
            not_sortable = [self._model.filter(x, user) for x in not_sortable]

        return calcs + not_sortable

    find_calc.description = (
        Description('Search for particular calculation')
        .param(
            'moleculeId',
            'The moleculeId the calculations should be associated with',
            dataType='string', paramType='query', required=False)
        .param(
            'calculationType',
            'The type or types of calculation being searched for',
            dataType='string', paramType='query', required=False)
        .param(
            'basis',
            'The basis set used for the calculations.',
             dataType='string', paramType='query', required=False)
        .param(
            'functional',
            'The functional used for the calculations.',
             dataType='string', paramType='query', required=False)
        .param(
            'theory',
            'The theory used for the calculations.',
             dataType='string', paramType='query', required=False)
        .param(
            'pending',
            'Whether the calculation is currently running.',
             dataType='boolean', paramType='query', required=False)
        .param(
            'limit',
            'The max number of calculations to return',
             dataType='integer', paramType='query', default=50, required=False)
        .param(
            'sortByTheory',
            'Sort the result by theory "priority", "best" first.',
             dataType='boolean', paramType='query', default=False, required=False))


    @access.public
    def find_id(self, id, params):
        cal = self._model.load(id, level=AccessType.READ, user=getCurrentUser())
        if not cal:
            raise RestException('Calculation not found.', code=404)
        return cal
    find_id.description = (
        Description('Get the calculation by id')
        .param(
            'id',
            'The id of calculatino.',
            dataType='string', required=True, paramType='path'))

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

    @access.token
    @autoDescribeRoute(
        Description('Update the calculation properties.')
        .notes('Override the exist properties')
        .modelParam('id', 'The ID of the calculation.', model='calculation',
                    plugin='molecules', level=AccessType.ADMIN)
        .param('body', 'The new set of properties', paramType='body')
        .errorResponse('ID was invalid.')
        .errorResponse('Write access was denied for the calculation.', 403)
    )
    def update_properties(self, calculation, params):
        props = getBodyJson()
        calculation['properties'] = props
        calculation = self._model.save(calculation)

        return calculation

    @access.user
    @autoDescribeRoute(
        Description('Add notebooks ( file ids ) to molecule.')
        .modelParam('id', 'The calculation id',
                    model=CalculationModel, destName='calculation',
                    force=True, paramType='path')
        .jsonParam('notebooks', 'List of notebooks', required=True, paramType='body')
    )
    def add_notebooks(self, calculation, notebooks):
        notebooks = notebooks.get('notebooks')
        if notebooks is not None:
            CalculationModel().add_notebooks(calculation, notebooks)
