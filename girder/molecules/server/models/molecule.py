# -*- coding: utf-8 -*-

import datetime
import json
import re

from girder.models.model_base import AccessControlledModel, ValidationException
from girder.constants import AccessType
from girder.plugins.molecules import avogadro
from girder.plugins.molecules import openbabel

class Molecule(AccessControlledModel):

    def __init__(self):
        super(Molecule, self).__init__()
        self.ensureIndex('properties.formula')

    def initialize(self):
        self.name = 'molecules'

    def validate(self, doc):
        return doc

    def findmol(self, search = None):
        limit, offset, sort = self._parse_pagination_params(search)

        query = {}
        if search:
            if 'name' in search:
                query['name'] = { '$regex': '^' + search['name'], '$options': 'i' }
            if 'inchi' in search:
                query['inchi'] = search['inchi']
            if 'inchikey' in search:
                query['inchikey'] = search['inchikey']
            if 'smiles' in search:
                # Make sure it is canonical before searching
                query['smiles'] = openbabel.to_smiles(search['smiles'], 'smi')

        cursor = self.find(query, limit=limit, offset=offset, sort=sort)
        mols = list()
        for mol in cursor:
            molecule = { '_id': mol['_id'], 'inchikey': mol.get('inchikey'),
                         'smiles': mol.get('smiles'),
                         'properties': mol.get('properties') }
            if 'name' in mol:
                molecule['name'] = mol['name']
            mols.append(molecule)

        return self._get_search_results_dict(mols, limit, offset, sort)

    def find_inchi(self, inchi):
        query = { 'inchi': inchi }
        mol = self.findOne(query)
        return mol

    def find_inchikey(self, inchikey):
        query = { 'inchikey': inchikey }
        mol = self.findOne(query)
        return mol

    def find_formula(self, formula, user, limit, offset, sort):
        formula_regx = re.compile('^%s$' % formula, re.IGNORECASE)
        query = {
            'properties.formula': formula_regx
        }
        mols = self.find(query, limit=limit, offset=offset, sort=sort)

        mols = list(self.filterResultsByPermission(mols, user,
                                                   level=AccessType.READ))

        return self._get_search_results_dict(mols, limit, offset, sort)

    def create(self, user, mol, public=False):

        if 'properties' not in mol and mol.get('cjson') is not None:
            props = avogadro.molecule_properties(json.dumps(mol.get('cjson')), 'cjson')
            mol['properties'] = props

        self.setUserAccess(mol, user=user, level=AccessType.ADMIN)
        if public:
            self.setPublic(mol, True)

        mol['created'] = datetime.datetime.utcnow()

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

    def _parse_pagination_params(self, params):
        """Parse params and get (limit, offset, sort)

        The defaults will be returned if not found in params.
        """
        # Defaults
        limit = 25
        offset = 0
        sort = [('created', -1)]
        if params:
            if 'limit' in params:
                limit = int(params['limit'])
            if 'offset' in params:
                offset = int(params['offset'])
            if 'sort' in params and 'sortdir' in params:
                sort = [(params['sort'], int(params['sortdir']))]

        return limit, offset, sort

    def _get_search_results_dict(self, mols, limit, offset, sort):
        """This is for consistent search results"""
        results = {
            'matches': len(mols),
            'limit': limit,
            'offset': offset,
            'results': mols
        }
        return results
