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
    cluster_id = str(event.info['_id'])

    # Use the first admin user we can find
    users = UserModel().find({'admin': True})
    if users.count() == 0:
        raise Exception('No admin users found. Cannot populate images')

    register_images(users[0], cluster_id)
