import json
from jsonschema import validate, ValidationError
from bson.objectid import ObjectId
import urllib
import urllib.parse

from girder.models.model_base import AccessControlledModel, ValidationException
from girder.constants import AccessType
from girder.models.file import File
from girder.models.item import Item
from girder.models.folder import Folder

from molecules.utilities.pagination import default_pagination_params
from molecules.utilities.pagination import search_results_dict

import openchemistry as oc

class Training(AccessControlledModel):
    '''
    {
        "input": {
            "parameters": {},
            "parametersHash": ""
        },
        "code": "",
        "image": {
            "repository": "",
            "tag": ""
        },
        "fileId": "",
        "properties": {},
        "notebooks": []
    }
    '''

    schema =  {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'required': ['input'],
        'properties': {
            'input': {
                'type': 'object',
                'properties': {
                    'parameters': {
                        'type': 'object'
                    },
                    'parametersHash': {
                        'type': 'string'
                    }
                }
            },
            'code': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string'
                    },
                    'version': {
                        'type': 'string'
                    }
                }
            },
            'image': {
                'type': 'object',
                'properties': {
                    'repository': {
                        'type': 'string'
                    },
                    'tag': {
                        'type': 'string'
                    }
                }
            },
            'fileId': {
                'type': 'string'
            },
            'properties': {
                'type': 'object'
            },
            "notebooks": {
                'type': 'array',
                'items': {
                    'type': 'string'
                }
            }
        }
    }

    def __init__(self):
        super(Training, self).__init__()

    def validate(self, doc):
        try:
            validate(doc, Training.schema)

        except ValidationError as ex:
            raise ValidationException(ex.message)

        return doc

    def initialize(self):
        self.name = 'trainings'
        self.ensureIndices([
            'properties.pending'
        ])

        self.exposeFields(level=AccessType.READ, fields=(
            '_id', 'fileId', 'properties',
            'notebooks', 'input', 'image', 'code'))

    def filter(self, training, user):
        training = super(Training, self).filter(doc=training, user=user)

        del training['_accessLevel']
        del training['_modelType']

        return training

    def create(self, user, props,
                     image=None, input_parameters=None,
                     notebooks=None, public=True):
        if notebooks is None:
            notebooks = []

        training = {
            'properties': props,
            'notebooks': notebooks
        }
        if image is not None:
            training['image'] = image
        if input_parameters is not None:
            training.setdefault('input', {})['parameters'] = input_parameters
            training.setdefault('input', {})['parametersHash'] = oc.hash_object(input_parameters)

        training['creatorId'] = user['_id']
        self.setUserAccess(training, user=user, level=AccessType.ADMIN)
        if public:
            self.setPublic(training, True)

        return self.save(training)

    def remove(self, training, user=None, force=False):
        super(Training, self).remove(training)
        # remove file with model data
        file_id = training.get('fileId')
        if file_id is not None:
            file = File().load(file_id, user=user, level=AccessType.WRITE)
            if file:
                item = Item().load(file['itemId'], user=user, level=AccessType.WRITE)
                if item:
                    Item().remove(item)
        # remove scratch folder with calculation output
        scratch_folder_id = training.get('scratchFolderId')
        if scratch_folder_id is not None:
            folder = Folder().load(scratch_folder_id, user=user, level=AccessType.WRITE)
            if folder:
                Folder().remove(folder)

    def find_model(self, image_name=None, input_parameters=None,
                creator_id=None, pending=None, limit=None,
                offset=None, sort=None, user=None):
        # Set these to their defaults if they are not already set
        limit, offset, sort = default_pagination_params(limit, offset, sort)

        query = {}

        if image_name:
            repository, tag = oc.parse_image_name(image_name)
            query['image.repository'] = repository
            query['image.tag'] = tag

        if input_parameters:
            input_json = json.loads(urllib.parse.unquote(input_parameters))
            query['input.parametersHash'] = oc.hash_object(input_json)

        if creator_id:
            query['creatorId'] = ObjectId(creator_id)

        if pending is not None:
            query['properties.pending'] = pending
            # The absence of the field mean the calculation is not pending ...
            if not pending:
                query['properties.pending'] = {
                    '$ne': True
                }

        fields = ['image', 'input', 'code',
                  'properties', 'fileId', 'access',
                  'public']

        trainings = self.find(query, fields=fields, limit=limit,
                                 offset=offset, sort=sort)
        num_matches = trainings.collection.count_documents(query)

        trainings = self.filterResultsByPermission(trainings, user,
            AccessType.READ, limit=limit)
        trainings = [self.filter(x, user) for x in trainings]

        return search_results_dict(trainings, num_matches, limit, offset, sort)
