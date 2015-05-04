# -*- coding: utf-8 -*-

import cherrypy
import json

from girder.api.describe import Description
from girder.api.docs import addModel
from girder.api.rest import Resource
from girder.api.rest import RestException
from girder.api import access

class Molecule(Resource):
    def __init__(self):
        self.resourceName = 'molecules'
        self.route('GET', (), self.find)
        self.route('GET', ('inchi', ':inchi'), self.find_inchi)
        self.route('POST', (), self.create)
        self.route('DELETE', ('inchi', ':inchi'), self.delete_inchi)

        self._model = self.model('molecule', 'molecules')

    def _clean(self, doc):
        del doc['access']
        doc['_id'] = str(doc['_id'])
        return doc

    @access.public
    def find(self, params):
        print "Find my molecule!"
        print params
        return { 'inchi': params.get('inchi', 'No InChI supplied!') }
    find.description = (
            Description('Find a molecule.')
            .param('inchi', 'The InChI of the molecule', paramType='query')
            .errorResponse())

    @access.public
    def find_inchi(self, inchi, params):
        print "Find my InChI!!!"
        print params
        mol = self._model.find_inchi(inchi)
        if not mol:
            raise RestException('Molecule not found.', code=404)
        return self._clean(mol)
    find_inchi.description = (
            Description('Find a molecule by inchi.')
            .param('inchi', 'The InChI of the molecule', paramType='path')
            .errorResponse()
           .errorResponse('Molecule not found.', 404))
    
    @access.user
    def create(self, params):
        body = json.loads(cherrypy.request.body.read())
        inchi = body['inchi']
        user = self.getCurrentUser()
        self._model.create(user, inchi)

    addModel('MoleculeParams', {
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
            required=True, paramType='body'))

    @access.user
    def delete_inchi(self, inchi, params):
        user = self.getCurrentUser()
        result = self._model.delete_inchi(user, inchi)
        if not result:
            raise RestException('Molecule not found.', code=404)
        return result
    delete_inchi.description = (
            Description('Delete a molecule by inchi.')
            .param('inchi', 'The InChI of the molecule', paramType='path')
            .errorResponse()
            .errorResponse('Molecule not found.', 404))

def load(info):
    info['apiRoot'].molecules = Molecule()
