import os
import glob
from bson.objectid import ObjectId

from girder import events
from girder.models.folder import Folder
from girder.models.upload import Upload
from girder.plugin import GirderPlugin
from girder.utility.path import lookUpPath

from .rest import Notebook

def createNotebooks(event):
    user = event.info
    folder_model = Folder()

    result = lookUpPath('user/%s/Private' % user['login'], force=True)
    private_folder = result['document']

    oc_folder = folder_model.createFolder(private_folder, 'oc',
                                          parentType='folder',
                                          creator=user,
                                          public=True,
                                          reuseExisting=True)

    notebook_folder = folder_model.createFolder(oc_folder, 'notebooks',
                                                parentType='folder',
                                                creator=user,
                                                public=True,
                                                reuseExisting=True)

    notebooks_dir = os.path.join(os.path.dirname(__file__), 'notebooks')

    upload_model = Upload()
    for file in glob.glob('%s/*.ipynb' % notebooks_dir):
        size =  os.path.getsize(file)
        name = os.path.basename(file)
        with open(file, 'rb') as fp:
            upload_model.uploadFromFile(
                fp, size=size, name=name, parentType='folder',
                parent={'_id': ObjectId(notebook_folder['_id'])}, user=user,
                mimeType='application/x-ipynb+json')

class NotebooksPlugin(GirderPlugin):
    DISPLAY_NAME = 'Sample Open Chemistry Notebooks'

    def load(self, info):
        events.bind('model.user.save.created', 'notebooks', createNotebooks)

        info['apiRoot'].notebooks = Notebook()
