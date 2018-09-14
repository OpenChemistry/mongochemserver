import cherrypy
import json
import os
import functools
import requests
from jsonpath_rw import parse

from girder.api.describe import Description, autoDescribeRoute
from girder.api.docs import addModel
from girder.api.rest import Resource
from girder.api.rest import RestException, loadmodel, getCurrentUser
from girder.api import access
from girder.constants import AccessType
from girder.constants import TerminalColor
from . import avogadro
from . import openbabel
from . import chemspider
from . import query
from . import semantic
from . import constants
from girder.plugins.molecules.models.molecule import Molecule as MoleculeModel

class Molecule(Resource):
    output_formats = ['cml', 'xyz', 'inchikey', 'sdf', 'cjson']
    input_formats = ['cml', 'xyz', 'sdf', 'cjson', 'json', 'log', 'nwchem', 'pdb']
    mime_types = {
        'cml': 'chemical/x-cml',
        'xyz': 'chemical/x-xyz',
        'sdf': 'chemical/x-mdl-sdfile',
        'cjson': 'application/json'
    }

    def __init__(self):
        super(Molecule, self).__init__()
        self.resourceName = 'molecules'
        self.route('GET', (), self.find)
        self.route('GET', ('inchikey', ':inchikey'), self.find_inchikey)
        self.route('GET', (':id', ':output_format'), self.get_format)
        self.route('GET', (':id', ), self.find_id)
        self.route('GET', ('search',), self.search)
        self.route('POST', (), self.create)
        self.route('DELETE', (':id',), self.delete)
        self.route('PATCH', (':id',), self.update)
        self.route('PATCH', (':id', 'notebooks'), self.add_notebooks)
        self.route('POST', ('conversions', ':output_format'), self.conversions)

        self._model = self.model('molecule', 'molecules')
        self._calc_model = self.model('calculation', 'molecules')

    def _clean(self, doc):
        del doc['access']
        if 'sdf' in doc:
            del doc['sdf']
        doc['_id'] = str(doc['_id'])
        if 'cjson' in doc:
            if 'basisSet' in doc['cjson']:
                del doc['cjson']['basisSet']
            if 'vibrations' in doc['cjson']:
                del doc['cjson']['vibrations']

        return doc

    @access.public
    def find(self, params):
        return self._model.findmol(params)
    find.description = (
            Description('Find a molecule.')
            .param('name', 'The name of the molecule', paramType='query',
                   required=False)
            .param('inchi', 'The InChI of the molecule', paramType='query',
                   required=False)
            .param('inchikey', 'The InChI key of the molecule', paramType='query',
                   required=False)
            .errorResponse())

    @access.public
    def find_inchikey(self, inchikey, params):
        mol = self._model.find_inchikey(inchikey)
        if not mol:
            raise RestException('Molecule not found.', code=404)
        return self._clean(mol)
    find_inchikey.description = (
            Description('Find a molecule by InChI key.')
            .param('inchikey', 'The InChI key of the molecule', paramType='path')
            .errorResponse()
           .errorResponse('Molecule not found.', 404))

    @access.public
    def find_id(self, id, params):
        mol = self._model.load(id, level=AccessType.READ, user=getCurrentUser())
        if not mol:
            raise RestException('Molecule not found.', code=404)
        return self._clean(mol)

    @access.user
    def create(self, params):
        body = self.getBodyJson()
        user = self.getCurrentUser()
        public = body.get('public', False)
        if 'fileId' in body:
            file_id = body['fileId']
            calc_id = body.get('calculationId')
            file = self.model('file').load(file_id, user=user)
            parts = file['name'].split('.')
            input_format = parts[-1]
            name = '.'.join(parts[:-1])

            if input_format not in Molecule.input_formats:
                raise RestException('Input format not supported.', code=400)

            contents = functools.reduce(lambda x, y: x + y, self.model('file').download(file, headers=False)())
            data_str = contents.decode()

            # Use the SDF format as it is the one with bonding that 3Dmol uses.
            output_format = 'sdf'

            if input_format == 'pdb':
                (output, _) = openbabel.convert_str(data_str, input_format, output_format)
            else:
                output = avogadro.convert_str(data_str, input_format, output_format)

            # Get some basic molecular properties we want to add to the database.
            props = avogadro.molecule_properties(data_str, input_format)
            pieces = props['spacedFormula'].strip().split(' ')
            atomCounts = {}
            for i in range(0, int(len(pieces) / 2)):
                atomCounts[pieces[2 * i ]] = int(pieces[2 * i + 1])

            cjson = []
            if input_format == 'cjson':
                cjson = json.loads(data_str)
            elif input_format == 'pdb':
                cjson = json.loads(avogadro.convert_str(output, 'sdf', 'cjson'))
            else:
                cjson = json.loads(avogadro.convert_str(data_str, input_format,
                                                        'cjson'))

            atom_count = openbabel.atom_count(data_str, input_format)

            if atom_count > 1024:
                raise RestException('Unable to generate inchi, molecule has more than 1024 atoms .', code=400)

            (inchi, inchikey) = openbabel.to_inchi(output, 'sdf')

            if not inchi:
                raise RestException('Unable to extract inchi', code=400)

            # Check if the molecule exists, only create it if it does.
            molExists = self._model.find_inchikey(inchikey)
            mol = {}
            if molExists:
                mol = molExists
            else:
                # Whitelist parts of the CJSON that we store at the top level.
                cjsonmol = {}
                cjsonmol['atoms'] = cjson['atoms']
                cjsonmol['bonds'] = cjson['bonds']
                cjsonmol['chemical json'] = cjson['chemical json']
                mol = self._model.create_xyz(user, {
                    'name': chemspider.find_common_name(inchikey, props['formula']),
                    'inchi': inchi,
                    'inchikey': inchikey,
                    output_format: output,
                    'cjson': cjsonmol,
                    'properties': props,
                    'atomCounts': atomCounts
                }, public)

                # Upload the molecule to virtuoso
                try:
                    semantic.upload_molecule(mol)
                except requests.ConnectionError:
                    print(TerminalColor.warning('WARNING: Couldn\'t connect to virtuoso.'))
        elif 'xyz' in body or 'sdf' in body:

            if 'xyz' in body:
                input_format = 'xyz'
                data = body['xyz']
            else:
                input_format = 'sdf'
                data = body['sdf']

            (inchi, inchikey) = openbabel.to_inchi(data, input_format)
            formula = openbabel.get_formula(data, input_format)

            properties = {
              'formula': formula
            }

            mol = {
                'inchi': inchi,
                'inchikey': inchikey,
                input_format: data,
                'properties': properties
            }

            if 'name' in body:
                mol['name'] = body['name']

            mol = self._model.create_xyz(user, mol, public)
        elif 'inchi' in body:
            inchi = body['inchi']
            formula = openbabel.get_formula(inchi, 'inchi')
            mol = self._model.create(user, inchi, formula, public=public)
        else:
            raise RestException('Invalid request', code=400)

        return self._clean(mol)

    addModel('Molecule', 'MoleculeParams', {
        "id": "MoleculeParams",
        "required": ["name", "inchi"],
        "properties": {
            "name": {"type": "string", "description": "The common name of the molecule"},
            "inchi": {"type": "string", "description": "The InChI of the molecule."}
        }
    })
    create.description = (
        Description('Create a molecule')
        .param(
            'body',
            'The molecule to be added to the database.',
            dataType='MoleculeParams',
            required=True, paramType='body')
        .errorResponse('Input format not supported.', code=400))

    @access.user
    def delete(self, id, params):
        user = self.getCurrentUser()
        mol = self._model.load(id, user=user, level=AccessType.WRITE)

        if not mol:
            raise RestException('Molecule not found.', code=404)

        return self._model.remove(mol)

    delete.description = (
            Description('Delete a molecule by id.')
            .param('id', 'The id of the molecule', paramType='path')
            .errorResponse()
            .errorResponse('Molecule not found.', 404))

    @access.user
    def update(self, id, params):
        user = self.getCurrentUser()

        mol = self._model.load(id, user=user, level=AccessType.WRITE)

        if not mol:
            raise RestException('Molecule not found.', code=404)

        body = self.getBodyJson()

        # TODO this should be refactored to use $addToSet
        if 'logs' in body:
            logs = mol.setdefault('logs', [])
            logs += body['logs']

        mol = self._model.update(mol)

        return self._clean(mol)
    addModel('Molecule', 'UpdateMoleculeParams', {
        "id": "UpdateMoleculeParams",
        "properties": {
            "logs": {"type": "array", "description": "List of Girder file ids"}
        }
    })
    update.description = (
            Description('Update a molecule by id.')
            .param('id', 'The id of the molecule', paramType='path')
            .param(
            'body',
            'The update to the molecule.',
            dataType='UpdateMoleculeParams',
            required=True, paramType='body')
            .errorResponse('Molecule not found.', 404))

    @access.user
    @autoDescribeRoute(
        Description('Add notebooks ( file ids ) to molecule.')
        .modelParam('id', 'The molecule id',
                    model=MoleculeModel, destName='molecule',
                    force=True, paramType='path')
        .jsonParam('notebooks', 'List of notebooks', required=True, paramType='body')
    )
    def add_notebooks(self, molecule, notebooks):
        notebooks = notebooks.get('notebooks')
        if notebooks is not None:
            MoleculeModel().add_notebooks(molecule, notebooks)

    @access.user
    def conversions(self, output_format, params):
        user = self.getCurrentUser()

        if output_format not in Molecule.output_formats:
            raise RestException('Output output_format not supported.', code=404)

        body = self.getBodyJson()

        if 'fileId' not in body:
            raise RestException('Invalid request body.', code=400)

        file_id = body['fileId']

        file = self.model('file').load(file_id, user=user)

        input_format = file['name'].split('.')[-1]

        if input_format not in Molecule.input_formats:
            raise RestException('Input format not supported.', code=400)

        if file is None:
            raise RestException('File not found.', code=404)

        contents = functools.reduce(lambda x, y: x + y, self.model('file').download(file, headers=False)())
        data_str = contents.decode()

        if output_format.startswith('inchi'):
            atom_count = 0
            if input_format == 'pdb':
                atom_count = openbabel.atom_count(data_str, input_format)
            else:
                atom_count = avogadro.atom_count(data_str, input_format)

            if atom_count > 1024:
                raise RestException('Unable to generate InChI, molecule has more than 1024 atoms.', code=400)

            if input_format == 'pdb':
                (inchi, inchikey) = openbabel.to_inchi(data_str, input_format)
            else:
                sdf = avogadro.convert_str(data_str, input_format, 'sdf')
                (inchi, inchikey) = openbabel.to_inchi(sdf, 'sdf')

            if output_format == 'inchi':
                return inchi
            else:
                return inchikey

        else:
            output = ''
            mime = 'text/plain'
            if input_format == 'pdb':
                (output, mime) = openbabel.convert_str(data_str, input_format, output_format)
            else:
                output = avogadro.convert_str(data_str, input_format, output_format)

            def stream():
                cherrypy.response.headers['Content-Type'] = mime
                yield output

            return stream

    addModel('Molecule', 'ConversionParams', {
        "id": "ConversionParams",
        "properties": {
            "fileId": {"type": "string", "description": "Girder file id to do conversion on"}
        }
    })
    conversions.description = (
            Description('Update a molecule by id.')
            .param('format', 'The format to convert to', paramType='path')
            .param(
            'body',
            'Details of molecule data to perform conversion on',
            dataType='ConversionParams',
            required=True, paramType='body')
            .errorResponse('Output format not supported.', 404)
            .errorResponse('File not found.', 404)
            .errorResponse('Invalid request body.', 400)
            .errorResponse('Input format not supported.', code=400))

    @access.public
    def get_format(self, id, output_format, params):
        # For now will for force load ( i.e. ignore access control )
        # This will change when we have access controls.
        molecule = self._model.load(id, force=True)

        if output_format not in Molecule.output_formats:
            raise RestException('Format not supported.', code=400)

        data = json.dumps(molecule['cjson'])
        if output_format != 'cjson':
            data = avogadro.convert_str(data, 'cjson', output_format)

        def stream():
            cherrypy.response.headers['Content-Type'] = Molecule.mime_types[output_format]
            yield data

        return stream

    get_format.description = (
            Description('Get molecule in particular format.')
            .param('id', 'The id of the molecule', paramType='path')
            .param('output_format', 'The format to convert to', paramType='path')
            .errorResponse('Output format not supported.', 400))

    @access.public
    def search(self, params):

        query_string = params.get('q')
        formula = params.get('formula')
        cactus = params.get('cactus')
        if query_string is None and formula is None and cactus is None:
            raise RestException('Either \'q\', \'formula\' or \'cactus\' is required.')

        if query_string is not None:
            try:
                mongo_query = query.to_mongo_query(query_string)
            except query.InvalidQuery:
                raise RestException('Invalid query', 400)

            mols = []
            for mol in self._model.find(query=mongo_query, fields = ['_id', 'inchikey', 'name']):
                mol['id'] = mol['_id']
                del mol['_id']
                mols.append(mol)

            return mols

        elif formula:
            # Search using formula
            return list(self._model.find_formula(formula, getCurrentUser()))
        elif cactus:
            # Disable cert verification for now
            # TODO Ensure we have the right root certs so this just works.
            r = requests.get('https://cactus.nci.nih.gov/chemical/structure/%s/sdf' % cactus, verify=False)

            if r.status_code == 404:
                return []
            else:
                r.raise_for_status()

            (inchi, inchikey) = openbabel.to_inchi(r.content.decode('utf8'), 'sdf')

            # See if we already have a molecule
            mol = self._model.find_inchikey(inchikey)

            # Create new molecule
            if mol is None:

                cjson_str = avogadro.convert_str(r.content, 'sdf', 'cjson')
                mol = {
                    'cjson': json.loads(cjson_str),
                    'inchikey': inchikey,
                    'origin': 'cactus'
                }

                user = getCurrentUser()
                if user is not None:
                    mol = self._model.create_xyz(getCurrentUser(), mol, public=True)

            return [mol]


    search.description = (
            Description('Search for molecules using a query string or formula')
            .param('q', 'The query string to use for this search', paramType='query', required=False)
            .param('formula', 'The formula (using the "Hill Order") to search for', paramType='query', required=False)
            .param('cactus', 'The identifier to pass to cactus', paramType='query', required=False))
