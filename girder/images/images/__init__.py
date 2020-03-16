from girder.plugin import GirderPlugin

from .image import Image


class ImagesPlugin(GirderPlugin):
    DISPLAY_NAME = 'OpenChemistry Images'

    def load(self, info):
        info['apiRoot'].images = Image()
