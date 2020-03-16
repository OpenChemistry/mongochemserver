from girder.constants import AccessType
from girder.exceptions import ValidationException
from girder.models.model_base import AccessControlledModel

from images.utils.pagination import parse_pagination_params
from images.utils.pagination import search_results_dict


class ImageTypes:
    DOCKER = 'docker'
    SINGULARITY = 'singularity'
    SHIFTER = 'shifter'
    TYPES = [DOCKER, SINGULARITY, SHIFTER]


class Image(AccessControlledModel):

    def initialize(self):
        self.name = 'images'

    def validate(self, doc):
        # Make sure this doesn't already exist. Otherwise, raise an
        # exception.
        fields = ['type', 'repository', 'tag', 'digest']
        query = {x: doc[x] for x in fields if x in doc}
        cursor = self.find(query, fields=fields, limit=1)
        images = [x for x in cursor]

        if len(images) != 0:
            raise ValidationException('An identical image already exists')

        return doc

    def find_image(self, params=None, user=None):
        if params is None:
            params = {}

        limit, offset, sort = parse_pagination_params(params)

        # This is for query fields that can just be copied over directly
        query_fields = ['type', 'repository', 'tag', 'digest']
        query_fields = [x for x in query_fields if params.get(x) is not None]
        query = {x: params[x] for x in query_fields}

        # This is for the returned fields
        fields = ['type', 'repository', 'tag', 'digest']

        cursor = self.findWithPermissions(query, fields=fields, limit=limit,
                                          offset=offset, sort=sort, user=user)

        num_matches = cursor.collection.count_documents(query)

        images = [x for x in cursor]
        return search_results_dict(images, num_matches, limit, offset, sort)

    def create(self, type, repository, tag, digest, user):
        image = {
          'type': type,
          'repository': repository,
          'tag': tag,
          'digest': digest,
          'creatorId': user.get('_id')
        }

        self.setUserAccess(image, user=user, level=AccessType.ADMIN)

        # These are always public currently
        self.setPublic(image, True)

        self.save(image)
        return image

    def remove_all(self, user):
        cursor = self.findWithPermissions({}, fields=[], user=user,
                                          level=AccessType.ADMIN)
        for image in cursor:
            self.remove(image)
