from girder.api.describe import Description
from girder.api.rest import Resource
from girder.api import access

class Molecule(Resource):
    def __init__(self):
        self.resourceName = 'molecules'
        self.route('GET', (), self.find)
        self.route('GET', ('inchi', ':inchi'), self.find_inchi)

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
        return { 'inchi': inchi }
    find_inchi.description = (
            Description('Find a molecule by inchi.')
            .param('inchi', 'The InChI of the molecule', paramType='path')
            .errorResponse())

def load(info):
    info['apiRoot'].molecules = Molecule()
