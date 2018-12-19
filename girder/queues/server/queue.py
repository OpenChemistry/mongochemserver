import cherrypy

from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource
from girder.api.rest import RestException, loadmodel, getCurrentUser
from girder.constants import AccessType, TokenScope
from girder.constants import TerminalColor
from girder.models.file import File

from girder.plugins.queues.models.queue import Queue as QueueModel
from girder.plugins.taskflow.models.taskflow import Taskflow as TaskflowModel

from cumulus.taskflow import load_class
import cumulus

class QueueType(object):
    FIFO = 'fifo'
    LIFO = 'lifo'
    TYPES = [FIFO, LIFO]

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
        self.route('POST', (':id', 'popall'), self.pop_tasks)
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
        return QueueModel().remove(queue)

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
        if taskflow['_id'] in queue['pending']:
            return queue

        queue['pending'].append(taskflow['_id'])
        if body is not None:
            taskflowId = str(taskflow['_id'])
            queue['start_params'][taskflowId] = body
        return QueueModel().save(queue)

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('If the current number of running taskflows is < max_running, pop a taskflow from the queue and start running it.')
        .modelParam('id', 'The queue id',
                    model=QueueModel, destName='queue',
                    level=AccessType.WRITE, paramType='path')
    )
    def pop_task(self, queue):
        queue, taskflowId, start_params = self._pop_one(queue)
        if taskflowId is not None:
            self._start_taskflow(taskflowId, start_params)

        return queue

    @access.user(scope=TokenScope.DATA_WRITE)
    @autoDescribeRoute(
        Description('Pop as many taskflows from the queue as needed to fill max_running slots.')
        .modelParam('id', 'The queue id',
                    model=QueueModel, destName='queue',
                    level=AccessType.WRITE, paramType='path')
    )
    def pop_tasks(self, queue):
        start = []
        queue, taskflowId, start_params = self._pop_one(queue)
        while taskflowId is not None:
            start.append({'taskflowId': taskflowId, 'start_params': start_params})
            queue, taskflowId, start_params = self._pop_one(queue)

        for task in start:
            self._start_taskflow(task['taskflowId'], task['start_params'])

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
        try:
            queue['running'].remove(taskflow['_id'])
            return QueueModel().save(queue)
        except ValueError:
            return queue

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

    def _pop_one(self, queue):
        taskflowId = None
        start_params = None
        pending = queue['pending']
        running = queue['running']
        max_running = queue['max_running']
        if ((max_running > 0 and len(running) >= max_running)
            or len(pending) == 0):
            return queue, taskflowId, start_params

        if queue['type'] == QueueType.FIFO:
            taskflowId = pending.pop(0)
        else:
            taskflowId = pending.pop()
        running.append(taskflowId)
        start_params = {}
        taskflowId_str = str(taskflowId)
        if taskflowId_str in queue['start_params']:
            start_params = queue['start_params'][taskflowId_str]
            del queue['start_params'][taskflowId_str]
        queue = QueueModel().save(queue)

        return queue, taskflowId, start_params

    def _start_taskflow(self, taskflowId, params=None):
        taskflow = TaskflowModel().load(taskflowId, user=self.getCurrentUser())

        constructor = load_class(taskflow['taskFlowClass'])
        token = self.model('token').createToken(user=self.getCurrentUser(), days=7)

        workflow = constructor(
            id=str(taskflow['_id']),
            girder_token=token['_id'],
            girder_api_url=cumulus.config.girder.baseUrl
        )

        if params is None:
            params = {}

        workflow.start(**params)

        return workflow
