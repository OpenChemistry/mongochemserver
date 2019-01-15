import cherrypy
import sys

from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource
from girder.api.rest import RestException, loadmodel, getCurrentUser
from girder.constants import AccessType, TokenScope
from girder.constants import TerminalColor
from girder.models.file import File

from girder.plugins.queues.models.queue import Queue as QueueModel
from girder.plugins.queues.models.queue import QueueType, TaskStatus
from girder.plugins.taskflow.models.taskflow import Taskflow as TaskflowModel

from cumulus.taskflow import load_class
import cumulus

class Queue(Resource):

    def __init__(self):
        super(Queue, self).__init__()
        self.resourceName = 'queues'
        self.route('GET', (), self.find)
        self.route('POST', (), self.create)
        self.route('GET', (':id', ), self.find_id)
        self.route('DELETE', (':id', ), self.remove)
        self.route('PUT', (':id', 'add', ':taskflowId'), self.add_task)
        self.route('PUT', (':id', 'pop'), self.pop_task)
        self.route('GET', (':id', 'taskflows'), self.get_tasks)

    @access.user(scope=TokenScope.DATA_READ)
    @autoDescribeRoute(
        Description('Find a queue')
        .param('name', 'A specific queue name', required=False)
        .pagingParams(defaultSort=None)
    )
    def find(self, name):
        return list(QueueModel().find(name=name, user=self.getCurrentUser()))

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Create a queue.')
        .param('name', 'The queue name')
        .param('type', 'The queue type', required=False)
        .param('maxRunning', 'The max number of taskflows that can be running at the same time', required=False, dataType='integer', default=0)
    )
    def create(self, name, type, maxRunning):
        if type is None or type.lower() not in QueueType.TYPES:
            type = QueueType.FIFO

        try:
            maxRunning = int(maxRunning)
        except ValueError:
            maxRunning = 0

        queue = QueueModel().create(name, type_=type, max_running=maxRunning, user=self.getCurrentUser())
        cherrypy.response.status = 201
        return queue

    @access.user(scope=TokenScope.DATA_READ)
    @autoDescribeRoute(
        Description('Fetch a queue.')
        .modelParam('id', 'The queue id',
                    model=QueueModel, destName='queue',
                    level=AccessType.READ, paramType='path')
    )
    def find_id(self, queue):
        return queue

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Delete a queue.')
        .modelParam('id', 'The queue id',
                    model=QueueModel, destName='queue',
                    level=AccessType.WRITE, paramType='path')
    )
    def remove(self, queue):
        QueueModel().remove(queue)
        cherrypy.response.status = 204
        return

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Add a taskflow to the queue.')
        .modelParam('id', 'The queue id',
                    model=QueueModel, destName='queue',
                    level=AccessType.WRITE, paramType='path')
        .modelParam('taskflowId', 'The taskflow id',
                    model=TaskflowModel, destName='taskflow',
                    level=AccessType.WRITE, paramType='path')
        .jsonParam('body', 'The taskflow start parameters', required=False, paramType='body')
    )
    def add_task(self, queue, taskflow, body):
        queue = QueueModel().add(queue, taskflow, body, self.getCurrentUser())
        return queue

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Pop a task from the queue if there are availabe run slots')
        .modelParam('id', 'The queue id',
                    model=QueueModel, destName='queue',
                    level=AccessType.WRITE, paramType='path')
        .param('multi', 'Pop as many tasks as needed to fill the run slots', dataType='boolean', default=False, required=False)
    )
    def pop_task(self, queue, multi):
        if multi:
            limit = sys.maxsize
        else:
            limit = 1

        queue = QueueModel().pop(queue, limit, user=self.getCurrentUser())

        return queue

    @access.user(scope=TokenScope.DATA_READ)
    @autoDescribeRoute(
        Description('Fetch the pending TaskFlows.')
        .modelParam('id', 'The queue id',
                    model=QueueModel, destName='queue',
                    level=AccessType.READ, paramType='path')
    )
    def get_tasks(self, queue):
        ids = queue['pending']
        query = {
            '_id': {
                '$in': ids
            }
        }
        taskflows = TaskflowModel().find(query)
        return taskflows

    @access.user(scope=TokenScope.DATA_READ)
    @autoDescribeRoute(
        Description('Fetch the pending TaskFlows.')
        .modelParam('id', 'The queue id',
                    model=QueueModel, destName='queue',
                    level=AccessType.READ, paramType='path')
        .param('status', 'Filter taskflows by status (%s|%s)' % (TaskStatus.RUNNING, TaskStatus.PENDING),
               required=False, default='')
    )
    def running_tasks(self, queue, status):
        if status not in [TaskStatus.RUNNING, TaskStatus.PENDING, '']:
            status = ''

        pending_ids = []
        running_ids = []

        include_pending = status in [TaskStatus.PENDING, '']
        include_running = status in [TaskStatus.RUNNING, '']

        for taskflow_id, taskflow_status in queue['taskflows'].items():
            if taskflow_status == TaskStatus.PENDING and include_pending:
                pending_ids.append(taskflow_id)
            elif taskflow_status == TaskStatus.RUNNING and include_running:
                running_ids.append(taskflow_id)

        query = {
            '_id': {
                '$in': running_ids + pending_ids
            }
        }
        taskflows = TaskflowModel().find(query)
        return taskflows
