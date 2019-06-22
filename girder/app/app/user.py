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

    # Get the updated user and return it
    # The added field is included
    user = User().findOne(user['_id'])
    return User().filter(user, getCurrentUser(), [field_name])


@access.public
@autoDescribeRoute(
    Description('Get the orcid of a user.')
    .modelParam('id', 'The ID of the user.', model=User, level=AccessType.READ)
)
def get_orcid(user):
    # Either orcidPublic must be true or the user has admin level access
    if user.get('orcidPublic') != True:
        if User().getAccessLevel(user, getCurrentUser()) != AccessType.ADMIN:
            return None

    return user.get('orcid')

@access.user
@autoDescribeRoute(
    Description('Set the orcid of a user.')
    .modelParam('id', 'The ID of the user.', model=User,
                level=AccessType.ADMIN)
    .param('orcid', 'The orcid to set.')
    .param('public', 'Whether or not the orcid is public.', dataType='boolean',
           required=False)
)
def set_orcid(user, orcid, public):
    if public is None:
        public = True

    _set_user_field(user, 'orcidPublic', public)
    return _set_user_field(user, 'orcid', orcid)


@access.public
@autoDescribeRoute(
    Description('Get the twitter username of a user.')
    .modelParam('id', 'The ID of the user.', model=User, level=AccessType.READ)
)
def get_twitter(user):
    # Either twitterPublic must be true or the user has admin level access
    if user.get('twitterPublic') != True:
        if User().getAccessLevel(user, getCurrentUser()) != AccessType.ADMIN:
            return None

    return user.get('twitter')


@access.user
@autoDescribeRoute(
    Description('Set the twitter username of a user.')
    .modelParam('id', 'The ID of the user.', model=User,
                level=AccessType.ADMIN)
    .param('twitter', 'The twitter username to set.')
    .param('public', 'Whether or not the twitter username is public.',
           dataType='boolean', required=False)
)
def set_twitter(user, twitter, public):
    if public is None:
        public = True

    _set_user_field(user, 'twitterPublic', public)
    return _set_user_field(user, 'twitter', twitter)
