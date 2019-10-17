from jsonpath_rw import parse


def get_cjson_energy(cjson):
    energy = parse('properties.totalEnergy').find(cjson)
    if energy:
        return energy[0].value
    return None
