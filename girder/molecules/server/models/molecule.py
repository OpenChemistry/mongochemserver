# -*- coding: utf-8 -*-

import re
import json

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
        cursor = self.find(query)
        mols = list()
        for mol in cursor:
            molecule = { '_id': mol['_id'], 'inchikey': mol.get('inchikey'),
                         'smiles': mol.get('smiles'), 'name': mol.get('name'),
                         'properties': mol.get('properties') }
            mols.append(molecule)
        return mols

    def find_inchi(self, inchi):
        query = { 'inchi': inchi }
        mol = self.findOne(query)
        return mol

    def find_inchikey(self, inchikey):
        query = { 'inchikey': inchikey }
        mol = self.findOne(query)
        return mol

    def find_formula(self, formula, user):
        formula_regx = re.compile('^%s$' % formula, re.IGNORECASE)
        query = {
            'properties.formula': formula_regx
        }
        mols = self.find(query)

        return self.filterResultsByPermission(mols, user, level=AccessType.READ)

    def create(self, user, mol, public=False):

        if 'properties' not in mol and mol.get('cjson') is not None:
            props = avogadro.molecule_properties(json.dumps(mol.get('cjson')), 'cjson')
            mol['properties'] = props

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
