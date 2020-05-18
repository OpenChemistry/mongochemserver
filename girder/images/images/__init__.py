from girder import events
from girder.models.user import User as UserModel
from girder.plugin import GirderPlugin

from images.image import Image
from images.utils.register_images import register_images


class ImagesPlugin(GirderPlugin):
    DISPLAY_NAME = 'OpenChemistry Images'

    def load(self, info):
        info['apiRoot'].images = Image()

        # When a cluster starts, register the images on that machine.
        events.bind('cumulus.cluster.started', 'images', populate_images)


def populate_images(event):
    cluster = event.info
    cluster_id = str(cluster['_id'])

    # We will register the images using the cluster creator
    creator_id = str(cluster['userId'])
    creator = UserModel().load(creator_id, force=True)

    register_images(creator, cluster_id)
