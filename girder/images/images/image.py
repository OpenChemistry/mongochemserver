import cherrypy

from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource, RestException
from girder.constants import AccessType, SortDir, TokenScope

from images.models.image import Image as ImageModel
from images.models.image import ImageTypes


class Image(Resource):

    def __init__(self):
        super(Image, self).__init__()
        self.resourceName = 'images'
        self.route('GET', (), self.find)
        self.route('GET', ('unique', ), self.find_unique)
        self.route('POST', (), self.create)
        self.route('GET', (':id', ), self.find_id)
        self.route('DELETE', (':id', ), self.remove)
        self.route('DELETE', (), self.remove_all)

    def _clean(self, doc):
        del doc['access']
        doc['_id'] = str(doc['_id'])
        return doc

    @access.user(scope=TokenScope.DATA_READ)
    @autoDescribeRoute(
        Description('Find image')
        .param('repository', 'Image repository', required=False)
        .param('tag', 'Image tag', required=False)
        .param('digest', 'Image digest', required=False)
        .pagingParams(defaultSort='_id',
                      defaultSortDir=SortDir.DESCENDING,
                      defaultLimit=25)
    )
    def find(self, **kwargs):
        return ImageModel().find_images(kwargs, user=self.getCurrentUser())

    @access.user(scope=TokenScope.DATA_READ)
    @autoDescribeRoute(
        Description('Find unique images (unique repository:tag combinations)')
        .param('repository', 'Image repository', required=False)
        .param('tag', 'Image tag', required=False)
        .param('digest', 'Image digest', required=False)
        .pagingParams(defaultSort='_id',
                      defaultSortDir=SortDir.DESCENDING,
                      defaultLimit=25)
    )
    def find_unique(self, **kwargs):
        return ImageModel().find_unique_images(kwargs,
                                               user=self.getCurrentUser())

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Create an image.')
        .param('type', 'Type of image (e.g. docker)', default='docker',
               lower=True)
        .param('repository', 'Image repository')
        .param('tag', 'Image tag')
        .param('digest', 'Image digest')
        .param('size', 'Image size in MB')
    )
    def create(self, type, repository, tag, digest, size):
        if type not in ImageTypes.TYPES:
            raise RestException('Invalid image type: ' + type)

        image = ImageModel().create(type=type, repository=repository,
                                    tag=tag, digest=digest, size=size,
                                    user=self.getCurrentUser())
        cherrypy.response.status = 201
        return self._clean(image)

    @access.user(scope=TokenScope.DATA_READ)
    @autoDescribeRoute(
        Description('Fetch an image.')
        .modelParam('id', 'The image id',
                    model=ImageModel, destName='image',
                    level=AccessType.READ, paramType='path')
    )
    def find_id(self, image):
        return self._clean(image)

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Delete an image.')
        .modelParam('id', 'The image id',
                    model=ImageModel, destName='image',
                    level=AccessType.WRITE, paramType='path')
    )
    def remove(self, image):
        ImageModel().remove(image)
        cherrypy.response.status = 204
        return

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Remove all images the user has permissions to remove.')
    )
    def remove_all(self):
        ImageModel().remove_all(self.getCurrentUser())
        cherrypy.response.status = 204
        return
