
from girder.api.describe import Description
from girder.api.docs import addModel
from girder.api import access
from girder.api.rest import Resource
from girder.api.rest import RestException, getBodyJson, getCurrentUser, \
    loadmodel
from girder.models.model_base import ModelImporter, ValidationException
from girder.constants import AccessType

from girder.plugins.molecules.models.experimental import Experimental

class Experiment(Resource):

    def __init__(self):
        super(Experiment, self).__init__()
        self.resourceName = 'experiments'
        self.route('GET', (), self.find_experiment)

        self._model = self.model('experimental', 'molecules')

    @access.public
    def find_experiment(self, params):
        user = getCurrentUser()

        query = { }
        if 'molecularFormula' in params:
            query['molecularFormula'] = params['molecularFormula']

        limit = int(params.get('limit', 50))
        experiments = self._model.find(query, limit=limit)

        return  [self._model.filter(x, user) for x in experiments]


    find_experiment.description = (
        Description('Get the calculation types available for the molecule')
        .param(
            'molecularFormula',
            'The molecular formula to search for experiments.',
            dataType='string', required=False, paramType='query')
        .param(
            'limit',
            'The max number of experiments to return',
             dataType='integer', paramType='query', default=50, required=False))

