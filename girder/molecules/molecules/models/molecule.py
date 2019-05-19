# -*- coding: utf-8 -*-

import json
from jsonpath_rw import parse
import re

from girder.models.model_base import AccessControlledModel, ValidationException
from girder.constants import AccessType
from molecules import avogadro
from molecules import openbabel

from molecules.utilities.pagination import parse_pagination_params
from molecules.utilities.pagination import search_results_dict

class Molecule(AccessControlledModel):

    def __init__(self):
        super(Molecule, self).__init__()
        self.ensureIndex('properties.formula')

    def initialize(self):
        self.name = 'molecules'

    def validate(self, doc):
        return doc

    def findmol(self, search = None):
        limit, offset, sort = parse_pagination_params(search)

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
            if 'creatorId' in search:
                query['creatorId'] = search['creatorId']

        cursor = self.find(query, limit=limit, offset=offset, sort=sort)
        mols = list()
        for mol in cursor:
            molecule = { '_id': mol['_id'], 'inchikey': mol.get('inchikey'),
                         'smiles': mol.get('smiles'),
                         'properties': mol.get('properties') }
            if 'name' in mol:
                molecule['name'] = mol['name']
            mols.append(molecule)

        return search_results_dict(mols, limit, offset, sort)

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

        return search_results_dict(mols, limit, offset, sort)

    def create(self, user, mol, public=False):

        if 'properties' not in mol and mol.get('cjson') is not None:
            props = avogadro.molecule_properties(json.dumps(mol.get('cjson')), 'cjson')
            mol['properties'] = props

        # This must be converted to a string, otherwise we will not be able to
        # search for it via query in self.find()
        mol['creatorId'] = str(user['_id'])

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

    def cjson_has_3d_coords(self, cjson):
        # jsonpath_rw won't let us parse "3d" because it has
        # issues parsing keys that start with a number...
        # If this changes in the future, fix this
        coords = parse('atoms.coords').find(cjson)
        if (coords and '3d' in coords[0].value and
            len(coords[0].value['3d']) > 0):
            return True
        return False

    def has_3d_coords(self, mol):
        # This functions properly if passed None
        return self.cjson_has_3d_coords(mol.get('cjson'))