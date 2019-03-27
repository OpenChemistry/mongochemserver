from girder.api.rest import RestException

def whitelist_cjson(cjson):
    # Find the cjson version key
    version_key = 'chemicalJson'
    if version_key not in cjson:
        if 'chemical json' in cjson:
            version_key = 'chemical json'
        else:
            raise RestException('No "chemicalJson" key found', 400)

    # Whitelist parts of the CJSON that we store at the top level.
    cjsonmol = {}
    cjsonmol['atoms'] = cjson['atoms']
    cjsonmol['bonds'] = cjson['bonds']
    cjsonmol['chemicalJson'] = cjson[version_key]

    return cjsonmol
