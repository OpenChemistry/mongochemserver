from jsonpath_rw import parse


def cjson_has_3d_coords(cjson):
    # jsonpath_rw won't let us parse "3d" because it has
    # issues parsing keys that start with a number...
    # If this changes in the future, fix this
    coords = parse('atoms.coords').find(cjson)
    if (coords and '3d' in coords[0].value and
            len(coords[0].value['3d']) > 0):
        return True
    return False
