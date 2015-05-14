# -*- coding: utf-8 -*-

from girder.models.model_base import AccessControlledModel, ValidationException
from girder.constants import AccessType

class Molecule(AccessControlledModel):

    def __init__(self):
        super(Molecule, self).__init__()

    def initialize(self):
        self.name = 'molecules'

    def validate(self, doc):
        return doc

    def findmol(self):
        cursor = self.find()
        mols = list()
        for mol in cursor:
            molecule = { 'id': mol['_id'], 'inchikey': mol['inchikey'],
                         'name': mol['name']}
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

    def create(self, user, inchi):
        mol = { 'inchi': inchi }
        self.setUserAccess(mol, user=user, level=AccessType.ADMIN)
        self.save(mol)
        return mol

    def create_xyz(self, user, mol):
        self.setUserAccess(mol, user=user, level=AccessType.ADMIN)
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
