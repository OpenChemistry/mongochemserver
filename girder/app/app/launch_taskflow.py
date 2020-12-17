import os
import sys

from girder.api import access
from girder.api.describe import autoDescribeRoute, Description
from girder.api.rest import getCurrentUser, getBodyJson, RestException
from girder.constants import TokenScope

from cumulus.taskflow import load_class
from cumulus_plugin.models.cluster import Cluster as ClusterModel
from queues.models.queue import Queue as QueueModel, QueueType
from taskflow.models.taskflow import Taskflow as TaskflowModel


@access.user(scope=TokenScope.DATA_WRITE)
@autoDescribeRoute(
    Description('Launch a taskflow.')
    .param('body',
           'Contains "taskFlowBody" and "taskFlowInput" for the taskflow and task',
           paramType='body')
)
def launch_taskflow_endpoint():
    user = getCurrentUser()
    body = getBodyJson()
    return launch_taskflow(user, body)


def launch_taskflow(user, body):
    # Perform some validation
    taskFlowBody = body.get('taskFlowBody')
    if taskFlowBody is None:
        raise RestException('taskFlowBody is a required key')

    if 'taskFlowClass' not in taskFlowBody:
        raise RestException('taskFlowClass is required in taskFlowBody')

    taskflow_class = taskFlowBody['taskFlowClass']

    # Check that we can load the taskflow class
    try:
        load_class(taskflow_class)
    except Exception as ex:
        msg = 'Unable to load taskflow class: %s (%s)' % \
              (taskflow_class, ex)
        raise RestException(msg, 400)

    # Set up the taskflow input
    taskFlowInput = body.get('taskFlowInput', {})
    if 'cluster' not in taskFlowInput:
        # Make a cluster
        taskFlowInput['cluster'] = create_cluster_object(user)

    if 'container' not in taskFlowInput:
        taskFlowInput['container'] = 'docker'

    # Load the queue
    queue = fetch_or_create_queue(user)

    # Create the taskflow
    taskflow = TaskflowModel().create(user, taskFlowBody)

    # Add it to the queue and start it
    QueueModel().add(queue, taskflow, taskFlowInput, user)
    QueueModel().pop(queue, limit=sys.maxsize, user=user)

    return taskflow['_id']


def _nersc():
    return os.environ.get('OC_SITE') == 'NERSC'


def fetch_or_create_queue(user):
    # Fetch or create the queue
    name = 'oc_queue'
    queues = list(QueueModel().find(name=name, user=user))
    if len(queues) > 0:
        queue = queues[0]
    else:
        type = QueueType.FIFO
        queue = QueueModel().create(name, type_=type, max_running=5, user=user)

    return queue


def create_cluster_object(user=None):
    if _nersc():
        return {'name': 'cori'}

    # Get the first cluster we can find
    clusters = ClusterModel().find_cluster({}, user=user)

    if len(clusters) > 0:
        return {'_id': clusters[0]['_id']}

    raise Exception('Unable to register images, no cluster configured')
