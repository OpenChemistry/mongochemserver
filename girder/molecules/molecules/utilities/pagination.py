

def parse_pagination_params(params):
    """Parse params and get (limit, offset, sort)
    The defaults will be returned if not found in params.
    """
    # Defaults
    limit = 25
    offset = 0
    sort = [('_id', -1)]
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
