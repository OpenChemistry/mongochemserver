from .queue import Queue

from girder.plugin import GirderPlugin

class QueuePlugin(GirderPlugin):
    DISPLAY_NAME = 'Taskflows Queue'

    def load(info):
        info['apiRoot'].queues = Queue()
