import datetime

from girder.api.rest import RestException
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
        image = self._get_base(doc.get('repository'), doc.get('tag'),
                               doc.get('digest'))
        if image is not None:
            raise ValidationException('An identical image already exists')

        return doc

    def find_images(self, params=None, user=None):
        if params is None:
            params = {}

        limit, offset, sort = parse_pagination_params(params)

        # This is for query fields that can just be copied over directly
        query_fields = ['repository', 'tag', 'digest']
        query_fields = [x for x in query_fields if params.get(x) is not None]
        query = {x: params[x] for x in query_fields}

        # This is for the returned fields
        fields = ['repository', 'tag', 'digest'] + ImageTypes.TYPES

        cursor = self.findWithPermissions(query, fields=fields, limit=limit,
                                          offset=offset, sort=sort, user=user)

        num_matches = cursor.collection.count_documents(query)

        images = [x for x in cursor]
        return search_results_dict(images, num_matches, limit, offset, sort)

    def find_unique_images(self, params=None, user=None):
        if params is None:
            params = {}

        limit, offset, sort = parse_pagination_params(params)

        # This is for query fields that can just be copied over directly
        query_fields = ['repository', 'tag', 'digest']
        query_fields = [x for x in query_fields if params.get(x) is not None]
        query = {x: params[x] for x in query_fields}

        # Get unique combinations of repositories and tags
        aggregate = []

        if query:
            aggregate.append({'$match': query})


        # Sort before grouping
        aggregate.append({'$sort': {sort[0][0]: sort[0][1]}})
        grouping = {
            '$group': {
                '_id': {
                    'repository': '$repository',
                    'tag': '$tag'
                },
                'sorted_id': {
                    '$first': '$_id'
                }
            }
        }
        aggregate.append(grouping)
        # Sort and apply the limit
        aggregate.append({'$sort': {'sorted_id': 1}})
        aggregate.append({'$limit': limit})

        # This is for the returned fields
        fields = ['repository', 'tag', 'digest'] + ImageTypes.TYPES

        or_query = []
        for unique in self.collection.aggregate(aggregate):
            or_query.append({'_id': unique['sorted_id']})

        query['$or'] = or_query
        cursor = self.findWithPermissions(query, fields=fields, limit=limit,
                                          offset=offset, sort=sort, user=user)
        images = [x for x in cursor]
        return search_results_dict(images, len(images), limit, offset, sort)

    def create(self, type, repository, tag, digest, size, user):
        if type not in ImageTypes.TYPES:
            raise RestException('Invalid image type: ' + type)

        image = self._get_or_create_base(repository, tag, digest, user)

        if type in image:
            raise RestException('Image already exists')

        # Write access is required
        self.requireAccess(image, user, AccessType.WRITE)

        body = {
            'size': size,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'creatorId': user.get('_id')
        }

        query = {
            '_id': image['_id']
        }

        updates = {
            '$set': {
                type: body
            },
        }

        super(Image, self).update(query, updates)

        # Reload the image
        return Image().load(image['_id'], user=user)

    def remove_all(self, user):
        cursor = self.findWithPermissions({}, fields=[], user=user,
                                          level=AccessType.ADMIN)
        for image in cursor:
            self.remove(image)

    def _create_base(self, repository, tag, digest, user):
        image = {
          'repository': repository,
          'tag': tag,
          'digest': digest,
          'creatorId': user.get('_id')
        }

        self.setUserAccess(image, user=user, level=AccessType.ADMIN)

        # These are always public currently
        self.setPublic(image, True)

        return self.save(image)

    def _get_base(self, repository, tag, digest):
        query = {
            'repository': repository,
            'tag': tag,
            'digest': digest
        }
        cursor = self.find(query, limit=1)
        imgs = [x for x in cursor]
        return imgs[0] if imgs else None

    def _get_or_create_base(self, repository, tag, digest, user):
        image = self._get_base(repository, tag, digest)
        if image is not None:
            return image

        return self._create_base(repository, tag, digest, user)
