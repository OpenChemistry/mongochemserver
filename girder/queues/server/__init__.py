from .queue import Queue

def load(info):
    info['apiRoot'].queues = Queue()
