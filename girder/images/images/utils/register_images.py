from app.launch_taskflow import launch_taskflow


def register_images(user, cluster_id=None):
    body = {
      'taskFlowBody': {
        'taskFlowClass': 'taskflows.ContainerListTaskFlow'
      },
      'taskBody': {
        'container': 'docker'
      }
    }

    if cluster_id:
        body['taskBody'].setdefault('cluster', {})['_id'] = cluster_id

    return launch_taskflow(user, body)
