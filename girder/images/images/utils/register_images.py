import os

from girder.models.token import Token as TokenModel
from girder.api.rest import getApiUrl
from girder_client import GirderClient


class TemporaryToken:
    # Create a temporary token for a user
    def __init__(self, user, days=1):
        self.user = user
        self.days = days
        self.token = None

    def __enter__(self):
        self.token = TokenModel().createToken(user=self.user, days=self.days)
        return self.token['_id']

    def __exit__(self, exception_type, exception_value, traceback):
        TokenModel().remove(self.token)


def _nersc():
    return os.environ.get('OC_SITE') == 'NERSC'


def fetch_or_create_queue(client):
    # Fetch or create the queue
    params = {'name': 'oc_queue'}
    queue = client.get('queues', parameters=params)

    if len(queue) > 0:
        queue = queue[0]
    else:
        params = {'name': 'oc_queue', 'maxRunning': 5}
        queue = client.post('queues', parameters=params)

    return queue


def create_cluster_object(client, cluster_id=None):
    if cluster_id is None and not _nersc():
        # Get the first cluster we can find
        params = {}
        clusters = client.get('clusters', params)

        if len(clusters) > 0:
            cluster_id = clusters[0]['_id']
        else:
            raise Exception('Unable to register images, no cluster configured')

    if cluster_id is not None:
        return {'_id': cluster_id}

    if _nersc():
        return {'name': 'cori'}

    raise Exception('Failed to configure cluster')


def register_images(user, cluster_id=None):

    with TemporaryToken(user) as token:
        client = GirderClient(apiUrl=getApiUrl())
        client.setToken(token)

        queue = fetch_or_create_queue(client)
        cluster = create_cluster_object(client, cluster_id)

        # Create the taskflow
        body = {
            'taskFlowClass': 'taskflows.ContainerListTaskFlow'
        }
        taskflow = client.post('taskflows', json=body)

        # Start the taskflow
        container = 'docker'
        body = {
            'cluster': cluster,
            'container': container
        }
        client.put('queues/%s/add/%s' % (queue['_id'], taskflow['_id']),
                   json=body)
        client.put('queues/%s/pop' % queue['_id'], parameters={'multi': True})

    return taskflow['_id']
