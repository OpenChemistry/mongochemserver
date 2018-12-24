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
from girder.plugins.queues.models.queue import QueueType
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
        self.route('POST', (':id', 'add', ':taskflowId'), self.add_task)
        self.route('POST', (':id', 'pop'), self.pop_task)
        self.route('POST', (':id', 'finish', ':taskflowId'), self.finish_task)
        self.route('GET', (':id', 'pending'), self.pending_tasks)
        self.route('GET', (':id', 'running'), self.running_tasks)

    @access.user(scope=TokenScope.DATA_READ)
    @autoDescribeRoute(
        Description('Find a queue')
        .param('name', 'A specific queue name', required=False)
        .pagingParams(defaultSort=None)
    )
    def find(self, name=None):
        return list(QueueModel().find(name=name, user=self.getCurrentUser()))

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Create a queue.')
        .param('name', 'The queue name', required=True)
        .param('type_', 'The queue type', required=False)
        .param('max_running', 'The max number of taskflows that can be running at the same time', required=False)
    )
    def create(self, name, type_=None, max_running=0):
        if type_ is None or type_.lower() not in QueueType.TYPES:
            type_ = QueueType.FIFO

        try:
            max_running = int(max_running)
        except ValueError:
            max_running = 0

        queue = QueueModel().create(name, type_=type_, max_running=max_running, user=self.getCurrentUser())
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
    def add_task(self, queue, taskflow, body=None):
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

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Mark a taskflow as complete.')
        .modelParam('id', 'The queue id',
                    model=QueueModel, destName='queue',
                    level=AccessType.WRITE, paramType='path')
        .modelParam('taskflowId', 'The taskflow id',
                    model=TaskflowModel, destName='taskflow',
                    level=AccessType.WRITE, paramType='path')
    )
    def finish_task(self, queue, taskflow):
        return QueueModel().finish(queue, taskflow, self.getCurrentUser())

    @access.user(scope=TokenScope.DATA_READ)
    @autoDescribeRoute(
        Description('Fetch the pending TaskFlows.')
        .modelParam('id', 'The queue id',
                    model=QueueModel, destName='queue',
                    level=AccessType.READ, paramType='path')
    )
    def pending_tasks(self, queue):
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
    )
    def running_tasks(self, queue):
        ids = queue['running']
        query = {
            '_id': {
                '$in': ids
            }
        }
        taskflows = TaskflowModel().find(query)
        return taskflows
