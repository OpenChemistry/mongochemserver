import pytest
import six
import os
import json

from girder.models.file import File
from girder.models.folder import Folder
from girder.models.upload import Upload

@pytest.fixture
def molecule():
    """Our method for creating a molecule within girder."""
    from molecules.models.molecule import Molecule
    from molecules import openbabel
    mols = []
    def _molecule(user, mol_name='ethane'):
        dir_path = os.path.dirname(os.path.realpath(__file__))

        with open(dir_path + '/data/' + mol_name + '.xyz', 'r') as rf:
            xyz_data = rf.read()

        input_format = 'xyz'
        data = xyz_data
        name = mol_name

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
        mols.append(mol)

        # These are normally performed in the molecule resource _clean() function
        del mol['access']
        mol['_id'] = str(mol['_id'])

        return mol

    yield _molecule

    # Delete mol
    for mol in mols:
        Molecule().remove(mol)

@pytest.fixture
def geometry():
    """Our method for creating a geometry within girder."""
    from molecules.models.geometry import Geometry

    geometries = []
    def _geometry(user, molecule):
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
        geometry = Geometry().create(user, molecule_id, cjson, 'user',
                                     user['_id'])
        geometries.append(geometry)

        # This is normally performed in a _clean() function
        del geometry['access']

        return geometry

    yield _geometry

    for geometry in geometries:
        # Delete the geometries
        Geometry().remove(geometry)

@pytest.fixture
def calculation():
    """Our method for creating a calculation within girder."""
    from molecules.models.calculation import Calculation
    calcs = []
    def _calculation(user, molecule, name='ethane'):

        assert '_id' in molecule

        dir_path = os.path.dirname(os.path.realpath(__file__))

        # This cjson should match the molecule
        with open(dir_path + '/data/'+ name + '.cjson', 'r') as rf:
            mol_cjson = json.load(rf)

        # Let's make some properties
        properties = {}
        if name == 'ethane':
            properties = {
                "molecular mass": 30.0690,
                "melting point": -172,
                "boiling point": -88
            }

        _calc = Calculation().create_cjson(user, mol_cjson, properties,
                                        molecule['_id'], notebooks=[],
                                        public=False)

        calc = Calculation().filter(_calc, user)
        calcs.append(calc)

        return calc

    yield _calculation

    # Delete calc
    for calc in calcs:
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
