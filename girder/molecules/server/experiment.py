import functools
import json
from jsonpath_rw import parse

from girder.api.describe import Description, autoDescribeRoute
from girder.api.docs import addModel
from girder.api import access
from girder.api.rest import Resource
from girder.api.rest import RestException, getBodyJson, getCurrentUser, \
    loadmodel
from girder.models.model_base import ModelImporter, ValidationException
from girder.models.file import File
from girder.constants import AccessType, TokenScope

from girder.plugins.molecules.models.experimental import Experimental


class Experiment(Resource):

    def __init__(self):
        super(Experiment, self).__init__()
        self.resourceName = 'experiments'
        self.route('POST', (), self.create)
        self.route('GET', (), self.find_experiment)

        self._model = self.model('experimental', 'molecules')

    def _process_experimental(self, doc):
        facility_used = parse('experiment.experimentalEnvironment.facilityUsed').find(doc)[0].value
        experiments = parse('experiment.experiments').find(doc)[0].value

        experiment_model = self.model('experimental', 'molecules')

        experiments_list = []
        for experiment in experiments:
            spectrum_type = experiment['spectrumType']
            experimental_technique = experiment['experimentalTechnique']
            id = experiment['id']
            molecular_formula = experiment['molecularFormula']
            instenisty_units = parse('measuredSpectrum.unitsY').find(experiment)[0].value
            frequency_units = parse('measuredSpectrum.unitsX').find(experiment)[0].value
            data_points = parse('measuredSpectrum.dataPoints').find(experiment)[0].value
            frequencies = data_points[::2]
            intensities = data_points[1::2]
            measured_spectrum = {
                'frequencies': {
                    'units': frequency_units,
                    'values': frequencies
                },
                'intensities': {
                    'units': instenisty_units,
                    'values': intensities
                }
            }

            experiments_list.append(experiment_model.create(
                facility_used, spectrum_type, experimental_technique, id,
                molecular_formula, measured_spectrum))

        return experiments_list

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Create an experiment.')
        .jsonParam('body', 'The experiment data', required=True, paramType='body')
    )
    def create(self, body):
        self.requireParams(['fileId'], body)

        file = File().load(body['fileId'], user=getCurrentUser())
        with File().open(file) as f:
            experiment_data = json.load(f)

        if 'experiment' not in experiment_data:
            raise RestException('Invalid experiment file.')

        return self._process_experimental(experiment_data)


    @access.public
    def find_experiment(self, params):
        user = getCurrentUser()

        if 'source' in params.keys():
            from .nist import search_nist_inchi, get_jdx
            from jcamp import jcamp_read

            inchi = params['inchi']      # TODO change API to accept
                                                    # a different key. From
                                                    # molecularFormula to inchi?
            stype = params['spectrum_type']
            nist_identifier =  search_nist_inchi(inchi)
            jdx = get_jdx(nist_identifier, stype=stype)

            ir = jcamp_read(jdx)
            return ir

        else:
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

