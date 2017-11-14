import nbformat
from nbconvert import HTMLExporter
import cherrypy

from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource, RestException
from girder.constants import AccessType, TokenScope
from girder.models.file import File

class Notebook(Resource):

    def __init__(self):
        self.resourceName = 'notebooks'
        super(Notebook, self).__init__()
        self.route('GET', (':fileId','html'), self.as_html)

    @access.public(scope=TokenScope.DATA_READ)
    @autoDescribeRoute(
        Description('Get a notebook as HTML ( uses nbconvert to perform the convertion ).')
        .modelParam('fileId', 'The file id for the notebook', model=File,
               paramType='path',  force=True)
        .errorResponse('ID was invalid.')
    )
    def as_html(self, file):
        with File().open(file) as fp:
            notebook = nbformat.reads(fp.read().decode(), as_version=4)

        exporter = HTMLExporter()
        #exporter.template_file = 'basic'

        (body, resources) = exporter.from_notebook_node(notebook)

        def stream():
            cherrypy.response.headers['Content-Type'] = 'text/html'
            yield body

        return stream
