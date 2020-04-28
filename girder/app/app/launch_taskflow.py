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
    .param('clusterId', 'The cluster ID to use.', required=False)
    .param('body',
           'Contains "taskFlowBody" and "taskBody" for the taskflow and task',
           paramType='body')
)
def launch_taskflow(clusterId):
    user = getCurrentUser()
    body = getBodyJson()

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

    # Set up the task body
    taskBody = body.get('taskBody', {})
    if 'cluster' not in taskBody:
        # Make a cluster
        taskBody['cluster'] = create_cluster_object(clusterId, user)

    if 'container' not in taskBody:
        taskBody['container'] = 'docker'

    # Load the queue
    queue = fetch_or_create_queue(user)

    # Create the taskflow
    taskflow = TaskflowModel().create(user, taskFlowBody)

    # Add it to the queue and start it
    QueueModel().add(queue, taskflow, taskBody, user)
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


def create_cluster_object(cluster_id=None, user=None):
    if cluster_id is None and not _nersc():
        # Get the first cluster we can find
        clusters = ClusterModel().find_cluster({}, user=user)

        if len(clusters) > 0:
            cluster_id = clusters[0]['_id']
        else:
            raise Exception('Unable to register images, no cluster configured')

    if cluster_id is not None:
        return {'_id': cluster_id}

    if _nersc():
        return {'name': 'cori'}

    raise Exception('Failed to configure cluster')
