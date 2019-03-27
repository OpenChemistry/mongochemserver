import json
import requests

from girder.api import access
from girder.constants import AccessType
from .. import avogadro
from .. import openbabel
from .. import chemspider
from .. import semantic
from .. import constants
from girder.plugins.molecules.models.molecule import Molecule as MoleculeModel
from girder.constants import TerminalColor

from .generate_3d_coords_async import schedule_3d_coords_gen
from .whitelist_cjson import whitelist_cjson

mol_formats_2d = [
    'smiles',
    'smi',
    'inchi'
]


def create_molecule(data_str, input_format, user, public):

    format_2d = (input_format in mol_formats_2d)
    smiles_format = 'smiles'

    if input_format == 'pdb':
        smiles = openbabel.to_smiles(data_str, input_format)
    elif input_format == 'inchi':
        smiles = openbabel.to_smiles(data_str, input_format)
    elif input_format == 'smi' or input_format == 'smiles':
        # This conversion still occurs to make sure we have canonical smiles
        smiles = openbabel.to_smiles(data_str, smiles_format)
    else:
        smiles = avogadro.convert_str(data_str, input_format, smiles_format)

    atom_count = openbabel.atom_count(smiles, smiles_format)

    if atom_count > 1024:
        raise RestException('Unable to generate inchi, '
                            'molecule has more than 1024 atoms .', code=400)

    (inchi, inchikey) = openbabel.to_inchi(smiles, smiles_format)

    if not inchi:
        raise RestException('Unable to extract inchi', code=400)

    # Check if the molecule exists, only create it if it does.
    molExists = MoleculeModel().find_inchikey(inchikey)
    mol = {}
    if molExists:
        mol = molExists
    else:
        # Get some basic molecular properties we want to add to the
        # database.
        props = avogadro.molecule_properties(smiles, smiles_format)
        pieces = props['spacedFormula'].strip().split(' ')
        atomCounts = {}
        for i in range(0, int(len(pieces) / 2)):
            atomCounts[pieces[2 * i]] = int(pieces[2 * i + 1])

        # Generate an svg file for an image
        svg_data = openbabel.to_svg(smiles, smiles_format)

        mol_dict = {
            'name': chemspider.find_common_name(inchikey, props['formula']),
            'inchi': inchi,
            'inchikey': inchikey,
            'smiles': smiles,
            'properties': props,
            'atomCounts': atomCounts,
            'svg': svg_data
        }

        cjson = {}
        if input_format == 'cjson':
            cjson = json.loads(data_str)
        else:
            if format_2d:
                # Generate 3d coordinates in a background thread
                schedule_3d_coords_gen(mol_dict, user)
                # This will be complete other than the cjson
                return MoleculeModel().create(user, mol_dict, public)
            else:
                sdf_data = openbabel.from_smiles(smiles, smiles_format)
                cjson = json.loads(avogadro.convert_str(sdf_data, 'sdf',
                                                        'cjson'))

        mol_dict['cjson'] = whitelist_cjson(cjson)

        mol = MoleculeModel().create(user, mol_dict, public)

        # Upload the molecule to virtuoso
        try:
            semantic.upload_molecule(mol)
        except requests.ConnectionError:
            print(TerminalColor.warning('WARNING: Couldn\'t connect to Jena.'))

    return mol
