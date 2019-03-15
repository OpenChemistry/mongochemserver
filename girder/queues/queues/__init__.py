from .queue import Queue

from girder.plugin import getPlugin, GirderPlugin

class QueuePlugin(GirderPlugin):
    DISPLAY_NAME = 'Taskflows Queue'

    def load(self, info):
        # Load dependency plugins
        getPlugin('cumulus_plugin').load(info)
        getPlugin('taskflow').load(info)

        info['apiRoot'].queues = Queue()
