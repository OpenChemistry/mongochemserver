from bson.objectid import ObjectId, InvalidId
from girder.constants import AccessType
from girder.models.model_base import AccessControlledModel
from girder.models.model_base import ValidationException

class Queue(AccessControlledModel):

    def initialize(self):
        self.name = 'queues'
        self.ensureIndices(['name'])

    def validate(self, queue):
        name = queue['name']
        userId = queue['userId']
        # Do we already have this name?
        if queue.get('_id') is None:
            if len(list(self.find(name=name, owner=userId, force=True))) > 0:
                raise ValidationException('"%s" has already been taken.' % name, field='name')
        return queue

    def find(self, name=None, owner=None, offset=0, limit=None, sort=None, user=None, force=False):
        query = {}

        if name is not None:
            query['name'] = name

        if owner is not None:
            if not isinstance(owner, ObjectId):
                try:
                    owner = ObjectId(owner)
                except InvalidId:
                    raise ValidationException('Invalid ObjectId: %s' % owner,
                                              field='owner')
            query['userId'] = owner

        cursor = super(Queue, self).find(query=query, sort=sort, user=user)

        if not force:
            for r in self.filterResultsByPermission(cursor=cursor, user=user,
                                                    level=AccessType.READ,
                                                    limit=limit, offset=offset):
                yield r
        else:
            for r  in cursor:
                yield r

    def create(self, name, type_, max_running, user=None):

        queue = {
            'name': name,
            'type': type_,
            'max_running': max_running,
            'pending': [],
            'running': [],
            'start_params': {}
        }

        userId = None
        if user is not None:
            userId = user['_id']
        
        queue['userId'] = userId

        self.setUserAccess(queue, user=user, level=AccessType.ADMIN)

        return self.save(queue)
