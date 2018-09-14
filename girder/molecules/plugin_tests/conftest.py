import pytest
import six

from girder.models.file import File
from girder.models.folder import Folder
from girder.models.upload import Upload


@pytest.fixture
def make_girder_file():
    files = []
    def _make_girder_file(assetstore, user, name, contents=b''):
        folder = Folder().find({
            'parentId': user['_id'],
            'name': 'Public'
        })[0]
        upload = Upload().uploadFromFile(
            six.BytesIO(contents), size=len(contents),
            name=name, parentType='folder', parent=folder,
            user=user, assetstore=assetstore)
        # finalizeUpload() does not get called automatically if the contents
        # are empty
        if not contents:
            file = Upload().finalizeUpload(upload, assetstore)
        else:
            file = upload

        files.append(file)

        return file

    yield _make_girder_file

    for file in files:
        File().remove(file)
