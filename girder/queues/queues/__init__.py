from .queue import Queue
from .models.queue import on_taskflow_status_update, cleanup_failed_taskflows

from girder import events
from girder.plugin import getPlugin, GirderPlugin

class QueuePlugin(GirderPlugin):
    DISPLAY_NAME = 'Taskflows Queue'

    def load(self, info):
        # Load dependency plugins
        getPlugin('cumulus_plugin').load(info)
        getPlugin('taskflow').load(info)

        info['apiRoot'].queues = Queue()

        # Remove taskflows that are not running anymore from the list of running
        # taskflows stored in the Queue model
        cleanup_failed_taskflows()

        # Listen to changes in the status of the taskflows, and update the Queues
        # if needed
        events.bind('cumulus.taskflow.status_update', 'queues', on_taskflow_status_update)
