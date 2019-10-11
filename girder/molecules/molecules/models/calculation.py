import sys
import json
from jsonschema import validate, ValidationError
from bson.objectid import ObjectId
import urllib
import urllib.parse

from girder.models.model_base import AccessControlledModel, ValidationException
from girder.utility.model_importer import ModelImporter
from girder.models.file import File
from girder.models.item import Item
from girder.models.folder import Folder
from girder.constants import AccessType
from molecules.utilities.pagination import default_pagination_params
from molecules.utilities.pagination import search_results_dict

from molecules.models.molecule import Molecule as MoleculeModel

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
            'moleculeId', 'properties.pending'
        ])

        self.exposeFields(level=AccessType.READ, fields=(
            '_id', 'moleculeId', 'fileId', 'properties', 'notebooks', 'input', 'image'))

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
            mol = ModelImporter.model('molecule', 'molecules').load(doc['moleculeId'],
                                                           force=True)
            doc['moleculeId'] = mol['_id']

        return doc

    def findcal(self, molecule_id=None, image_name=None,
                input_parameters=None, input_geometry_hash=None,
                name=None, inchi=None, inchikey=None, smiles=None,
                formula=None, creator_id=None, pending=None, limit=None,
                offset=None, sort=None, user=None):
        # Set these to their defaults if they are not already set
        limit, offset, sort = default_pagination_params(limit, offset, sort)

        query = {}

        # If a molecule id is specified it has higher priority
        if molecule_id:
            query['moleculeId'] = ObjectId(molecule_id)
        # Otherwise, if query parameters for the molecules are
        # specified, search for matching molecules first
        elif any((name, inchi, inchikey, smiles, formula)):
            params = {'offset': 0, 'limit': sys.maxsize}

            if name:
                params['name'] = name
            if inchi:
                params['inchi'] = inchi
            if inchikey:
                params['inchikey'] = inchikey
            if smiles:
                params['smiles'] = smiles
            if formula:
                params['formula'] = formula

            molecules = MoleculeModel().findmol(params)['results']
            molecule_ids = [molecule['_id'] for molecule in molecules]
            query['moleculeId'] = {'$in': molecule_ids}

        if image_name:
            repository, tag = oc.parse_image_name(image_name)
            query['image.repository'] = repository
            query['image.tag'] = tag

        if input_parameters:
            input_json = json.loads(urllib.parse.unquote(input_parameters))
            query['input.parametersHash'] = oc.hash_object(input_json)

        if input_geometry_hash:
            query['input.geometryHash'] = input_geometry_hash

        if creator_id:
            query['creatorId'] = ObjectId(creator_id)

        if pending is not None:
            pending = toBool(pending)
            query['properties.pending'] = pending
            # The absence of the field mean the calculation is not pending ...
            if not pending:
                query['properties.pending'] = {
                    '$ne': True
                }

        fields = ['image', 'input',
                  'cjson', 'cjson.vibrations.modes', 'cjson.vibrations.intensities',
                  'cjson.vibrations.frequencies', 'properties', 'fileId', 'access',
                  'moleculeId', 'public']

        calcs = self.find(query, fields=fields, limit=limit,
                                 offset=offset, sort=sort)
        num_matches = calcs.collection.count_documents(query)

        calcs = self.filterResultsByPermission(calcs, user,
            AccessType.READ, limit=limit)
        calcs = [self.filter(x, user) for x in calcs]

        return search_results_dict(calcs, num_matches, limit, offset, sort)

    def create_cjson(self, user, cjson, props, molecule_id= None,
                     image=None, input_parameters=None,
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
        if image is not None:
            calc['image'] = image
        if input_parameters is not None:
            calc.setdefault('input', {})['parameters'] = input_parameters
            calc.setdefault('input', {})['parametersHash'] = oc.hash_object(input_parameters)

        calc['creatorId'] = user['_id']
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

    def remove(self, calc, user=None, force=False):
        super(Calculation, self).remove(calc)
        # remove ingested file
        file_id = calc.get('fileId')
        if file_id is not None:
            file = File().load(file_id, user=user, level=AccessType.WRITE)
            if file:
                item = Item().load(file['itemId'], user=user, level=AccessType.WRITE)
                if item:
                    Item().remove(item)
        # remove scratch folder with calculation output
        scratch_folder_id = calc.get('scratchFolderId')
        if scratch_folder_id is not None:
            folder = Folder().load(scratch_folder_id, user=user, level=AccessType.WRITE)
            if folder:
                Folder().remove(folder)
