from girder.constants import SortDir

def default_pagination_params(limit=None, offset=None, sort=None):
    """Returns default params unless they are set"""
    if limit is None:
        limit = 25
    if offset is None:
        offset = 0
    if sort is None:
        sort = [('_id', SortDir.DESCENDING)]

    return limit, offset, sort

def parse_pagination_params(params):
    """Parse params and get (limit, offset, sort)
    The defaults will be returned if not found in params.
    """
    # Defaults
    limit, offset, sort = default_pagination_params()
    if params:
        if 'limit' in params:
            limit = int(params['limit'])
        if 'offset' in params:
            offset = int(params['offset'])
        if 'sort' in params and 'sortdir' in params:
            sort = [(params['sort'], int(params['sortdir']))]

    return limit, offset, sort


def search_results_dict(results, limit, offset, sort):
    """This is for consistent search results"""
    ret = {
        'matches': len(results),
        'limit': limit,
        'offset': offset,
        'results': results
    }
    return ret
