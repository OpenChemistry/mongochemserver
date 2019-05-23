from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import getCurrentUser
from girder.models.model_base import AccessType
from girder.models.user import User

def _set_user_field(user, field_name, field_value):
    query = {
        '_id': user['_id']
    }

    update = {
        '$set': {
            field_name: field_value
        }
    }

    User().update(query, update)

    return User().load(user['_id'], user=getCurrentUser())

@access.public
@autoDescribeRoute(
    Description('Get the orcid of a user.')
    .modelParam('id', 'The ID of the user.', model=User, level=AccessType.ADMIN)
)
def get_orcid(user):
    return user.get('orcid')

@access.user
@autoDescribeRoute(
    Description('Set the orcid of a user.')
    .modelParam('id', 'The ID of the user.', model=User, level=AccessType.READ)
    .param('orcid', 'The orcid to set.')
    .param('public', 'Whether or not the orcid is public.', dataType='boolean',
           required=False)
)
def set_orcid(user, orcid, public):
    return _set_user_field(user, 'orcid', orcid)

@access.public
@autoDescribeRoute(
    Description('Get the twitter username of a user.')
    .modelParam('id', 'The ID of the user.', model=User, level=AccessType.ADMIN)
)
def get_twitter(user):
    return user.get('twitter')

@access.user
@autoDescribeRoute(
    Description('Set the twitter username of a user.')
    .modelParam('id', 'The ID of the user.', model=User, level=AccessType.READ)
    .param('twitter', 'The twitter to set.')
    .param('public', 'Whether or not the twitter is public.', dataType='boolean',
           required=False)
)
def set_twitter(user, twitter, public):
    return _set_user_field(user, 'twitter', twitter)
