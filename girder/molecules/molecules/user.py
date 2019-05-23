from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import getCurrentUser
from girder.models.model_base import AccessType
from girder.models.user import User

@access.public
@autoDescribeRoute(
    Description('Set the orcid of a user.')
    .modelParam('id', 'The ID of the user.', model=User, level=AccessType.ADMIN)
)
def get_orcid(user):
    return user.get('orcid')

@access.user
@autoDescribeRoute(
    Description('Get the orcid of a user.')
    .modelParam('id', 'The ID of the user.', model=User, level=AccessType.READ)
    .param('orcid', 'The orcid to set.')
    .param('public', 'Whether or not the orcid is public.', dataType='boolean',
           required=False)
)
def set_orcid(user, orcid, public):
    query = {
        '_id': user['_id']
    }

    update = {
        '$set': {
            'orcid': orcid
        }
    }

    User().update(query, update)
