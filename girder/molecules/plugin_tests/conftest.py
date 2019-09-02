import pytest
import six
import os
import json

from girder.models.file import File
from girder.models.folder import Folder
from girder.models.upload import Upload

@pytest.fixture
def molecule(user):
    """Our method for creating a molecule within girder."""
    from molecules.models.molecule import Molecule
    from molecules import openbabel

    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(dir_path + '/data/ethane.xyz', 'r') as rf:
        xyz_data = rf.read()

    input_format = 'xyz'
    data = xyz_data
    name = 'ethane'

    (inchi, inchikey) = openbabel.to_inchi(data, input_format)
    smiles = openbabel.to_smiles(data, input_format)
    properties = openbabel.properties(data, input_format)

    mol = {
        'inchi': inchi,
        'inchikey': inchikey,
        'smiles': smiles,
        'name': name,
        'properties': properties,
        'cjson': {
            'atoms': {}
        }
    }

    mol = Molecule().create(user, mol, public=False)

    # These are normally performed in the molecule resource _clean() function
    del mol['access']
    mol['_id'] = str(mol['_id'])

    yield mol

    # Delete mol
    Molecule().remove(mol)


@pytest.fixture
def geometry(user, molecule):
    """Our method for creating a geometry within girder."""
    from girder.plugins.molecules.models.geometry import Geometry

    # The molecule will have been created by the fixture
    assert '_id' in molecule

    molecule_id = molecule['_id']

    # Get some cjson
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(dir_path + '/data/ethane.cjson', 'r') as rf:
        ethane_cjson = json.load(rf)

    # Whitelist the cjson to only contain the parts needed for geometry
    whitelist = ['atoms', 'bonds', 'chemical json']
    cjson = {}
    for item in whitelist:
        cjson[item] = ethane_cjson[item]

    # Create a geometry
    geometry = Geometry().create(user, molecule_id, json.dumps(cjson),
                                 'user', user['_id'])

    # This is normally performed in a _clean() function
    del geometry['access']

    yield geometry

    # Delete mol
    Geometry().remove(geometry)


@pytest.fixture
def calculation(user, molecule):
    """Our method for creating a calculation within girder."""
    from molecules.models.calculation import Calculation

    assert '_id' in molecule

    dir_path = os.path.dirname(os.path.realpath(__file__))

    # This cjson should match the molecule
    with open(dir_path + '/data/ethane.cjson', 'r') as rf:
        ethane_cjson = rf.read()

    # Let's make some properties
    properties = {
        "molecular mass": 30.0690,
        "melting point": -172,
        "boiling point": -88
    }

    _calc = Calculation().create_cjson(user, ethane_cjson, properties,
                                       molecule['_id'], notebooks=[],
                                       public=False)

    calc = Calculation().filter(_calc, user)

    yield calc

    # Delete calc
    Calculation().remove(calc)


@pytest.fixture
def make_girder_file():
    files = []
    def _make_girder_file(assetstore, user, name, contents=b''):
        folder = Folder().find({
            'parentId': user['_id'],
            'name': 'Public'
        })[0]
        upload = Upload().uploadFromFile(
            six.BytesIO(contents), size=len(contents),
            name=name, parentType='folder', parent=folder,
            user=user, assetstore=assetstore)
        # finalizeUpload() does not get called automatically if the contents
        # are empty
        if not contents:
            file = Upload().finalizeUpload(upload, assetstore)
        else:
            file = upload

        files.append(file)

        return file

    yield _make_girder_file

    for file in files:
        File().remove(file)
