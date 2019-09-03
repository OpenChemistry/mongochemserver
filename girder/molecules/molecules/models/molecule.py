# -*- coding: utf-8 -*-

from bson.objectid import ObjectId
import json
import re

from girder.models.model_base import AccessControlledModel
from girder.constants import AccessType
from girder.exceptions import RestException, ValidationException
from molecules import avogadro
from molecules import openbabel

from molecules import query as mol_query
from molecules.utilities.pagination import parse_pagination_params
from molecules.utilities.pagination import search_results_dict
from molecules.utilities.has_3d_coords import cjson_has_3d_coords

class Molecule(AccessControlledModel):

    def __init__(self):
        super(Molecule, self).__init__()
        self.ensureIndex('properties.formula')
        self.ensureIndex('inchikey')

    def initialize(self):
        self.name = 'molecules'

    def validate(self, doc):
        return doc

    def findmol(self, search = None):
        limit, offset, sort = parse_pagination_params(search)

        if search is None:
            search = {}

        query = {}
        if 'queryString' in search:
            # queryString takes precedence over all other search params
            query_string = search['queryString']
            try:
                query = mol_query.to_mongo_query(query_string)
            except mol_query.InvalidQuery:
                raise RestException('Invalid query', 400)
        elif search:
            # If the search dict is not empty, perform a search
            if 'name' in search:
                query['name'] = { '$regex': '^' + search['name'],
                                  '$options': 'i' }
            if 'inchi' in search:
                query['inchi'] = search['inchi']
            if 'inchikey' in search:
                query['inchikey'] = search['inchikey']
            if 'smiles' in search:
                # Make sure it is canonical before searching
                query['smiles'] = openbabel.to_smiles(search['smiles'], 'smi')
            if 'formula' in search:
                formula_regx = re.compile('^%s$' % search['formula'],
                                          re.IGNORECASE)
                query['properties.formula'] = formula_regx
            if 'creatorId' in search:
                query['creatorId'] = ObjectId(search['creatorId'])

            if 'minValues' in search:
                try:
                    minValues = json.loads(search['minValues'])
                    for key in minValues:
                        if key not in query:
                            query[key] = {}
                        query[key]['$gte'] = minValues[key]
                except:
                    raise RestException('Failed to parse minValues')

            if 'maxValues' in search:
                try:
                    maxValues = json.loads(search['maxValues'])
                    for key in maxValues:
                        if key not in query:
                            query[key] = {}
                        query[key]['$lte'] = maxValues[key]
                except:
                    raise RestException('Failed to parse maxValues')

        fields = [
          'inchikey',
          'smiles',
          'properties',
          'name'
        ]

        cursor = self.find(query, fields=fields, limit=limit, offset=offset,
                           sort=sort)

        num_matches = cursor.collection.count_documents(query)

        mols = [x for x in cursor]
        return search_results_dict(mols, num_matches, limit, offset, sort)

    def find_inchi(self, inchi):
        query = { 'inchi': inchi }
        mol = self.findOne(query)
        return mol

    def find_inchikey(self, inchikey):
        query = { 'inchikey': inchikey }
        mol = self.findOne(query)
        return mol

    def create(self, user, mol, public=False):

        if 'properties' not in mol and mol.get('cjson') is not None:
            props = avogadro.molecule_properties(json.dumps(mol.get('cjson')), 'cjson')
            mol['properties'] = props

        mol['creatorId'] = user['_id']

        self.setUserAccess(mol, user=user, level=AccessType.ADMIN)
        if public:
            self.setPublic(mol, True)

        self.save(mol)
        return mol

    def delete_inchi(self, user, inchi):
        mol = self.find_inchi(inchi)
        if not mol:
            return False
        else:
            return self.remove(mol)

    def update(self, mol):
        self.save(mol)

        return mol

    def add_notebooks(self, mol, notebooks):
        query = {
            '_id': mol['_id']
        }

        update = {
            '$addToSet': {
                'notebooks': {
                    '$each': notebooks
                }
            }
        }
        super(Molecule, self).update(query, update)

    def has_3d_coords(self, mol):
        # This functions properly if passed None
        return cjson_has_3d_coords(mol.get('cjson'))
