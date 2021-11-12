import cherrypy

from girder.api import access
from girder.api.docs import addModel
from girder.api.rest import Resource
from girder.api.rest import getCurrentUser, getBodyJson
from girder.constants import SortDir
from girder.constants import AccessType, TokenScope
from girder.api.describe import Description, autoDescribeRoute

from molecules.models.training import Training as TrainingModel

class Training(Resource):
    def __init__(self):
        super(Training, self).__init__()
        self.resourceName = 'trainings'
        self.route('GET', (), self.find_training)
        self.route('GET', (':id',), self.find_id)
        self.route('POST', (), self.create_training)
        self.route('PUT', (':id', ), self.ingest_training)
        self.route('PUT', (':id', 'properties'), self.update_properties)
        self.route('DELETE', (':id',), self.delete_training)

    @access.user(scope=TokenScope.DATA_WRITE)
    def create_training(self, params):
        body = getBodyJson()
        user = getCurrentUser()

        props = body.get('properties', {})
        public = body.get('public', True)
        notebooks = body.get('notebooks', [])
        image = body.get('image')
        input_parameters = body.get('input', {}).get('parameters')
        if input_parameters is None:
            input_parameters = body.get('inputParameters', {})

        training = TrainingModel().create(user, props,
                                          image=image,
                                          input_parameters=input_parameters,
                                          notebooks=notebooks, public=public)

        cherrypy.response.status = 201
        cherrypy.response.headers['Location'] \
            = '/trainings/%s' % (str(training['_id']))

        return TrainingModel().filter(training, user)

    # Try and reuse schema for documentation, this only partially works!
    training_schema = TrainingModel.schema.copy()
    training_schema['id'] = 'TrainingData'
    addModel('Training', 'TrainingData', training_schema)

    create_training.description = (
        Description('Create a new entity that represents a trained ML model.')
        .param(
            'body',
            'The training data', dataType='TrainingData', required=True,
            paramType='body'))

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Update pending training model with trained results.')
        .modelParam('id', 'The training id',
            model=TrainingModel, destName='training',
            level=AccessType.WRITE, paramType='path')
        .jsonParam('body', 'The training details', required=True, paramType='body')
    )
    def ingest_training(self, training, body):
        self.requireParams(['fileId'], body)

        # training['properties'] = body.get('properties', {})
        training['fileId'] = body.get('fileId')

        properties = training['properties']
        # The calculation is no longer pending
        if 'pending' in properties:
            del properties['pending']
        training['properties'] = properties

        image = body.get('image')
        if image is not None:
            training['image'] = image

        code = body.get('code')
        if code is not None:
            training['code'] = code

        return TrainingModel().save(training)

    @access.user(scope=TokenScope.DATA_WRITE)
    def delete_training(self, id, params):
        user = getCurrentUser()
        training = TrainingModel().load(id, level=AccessType.READ, user=user)
        if not training:
            raise RestException('Model not found.', code=404)

        return TrainingModel().remove(training, user)
    delete_training.description = (
        Description('Delete a trained model by id.')
        .param(
            'id',
            'The id of the model.',
            dataType='string', required=True, paramType='path'))

    @access.public
    def find_id(self, id, params):
        user = getCurrentUser()
        training = TrainingModel().load(id, level=AccessType.READ, user=user)
        if not training:
            raise RestException('Model not found.', code=404)

        return training
    find_id.description = (
        Description('Get the model by id')
        .param(
            'id',
            'The id of the model.',
            dataType='string', required=True, paramType='path'))

    @access.public
    @autoDescribeRoute(
        Description('Search for particular model')
        .param('imageName', 'The name of the Docker image that run this calculation', required=False)
        .param('inputParameters', 'JSON string of the input parameters. May be in percent encoding.', required=False)
        .param('creatorId', 'The id of the user that created the calculation',
               required=False)
        .pagingParams(defaultSort='_id', defaultSortDir=SortDir.DESCENDING, defaultLimit=25)
    )
    def find_training(self, imageName=None, inputParameters=None,
                   creatorId=None, pending=None,
                   limit=None, offset=None, sort=None):
        return TrainingModel().find_model(
            image_name=imageName, input_parameters=inputParameters,
            creator_id=creatorId, pending=pending, limit=limit, offset=offset,
            sort=sort, user=getCurrentUser())

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Update the model properties.')
        .notes('Override the exist properties')
        .modelParam('id', 'The ID of the model.', model='training',
                    plugin='molecules', level=AccessType.ADMIN)
        .param('body', 'The new set of properties', paramType='body')
        .errorResponse('ID was invalid.')
        .errorResponse('Write access was denied for the calculation.', 403)
    )
    def update_properties(self, training, params):
        props = getBodyJson()
        training['properties'] = props
        training = TrainingModel().save(training)

        return training
