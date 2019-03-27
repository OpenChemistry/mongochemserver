import json
import requests

from .. import avogadro
from .. import openbabel
from .. import chemspider
from .. import semantic
from girder.plugins.molecules.models.molecule import Molecule as MoleculeModel
from girder.constants import TerminalColor
from girder.api.rest import RestException

from .generate_3d_coords_async import schedule_3d_coords_gen
from .whitelist_cjson import whitelist_cjson

openbabel_2d_formats = [
    'smiles',
    'smi',
    'inchi'
]

# Add more to this list if we want open babel to convert them
# rather than avogadro.
openbabel_3d_formats = [
  'pdb'
]


def create_molecule(data_str, input_format, user, public):

    using_2d_format = (input_format in openbabel_2d_formats)
    smiles_format = 'smiles'

    if using_2d_format or input_format in openbabel_3d_formats:
        smiles = openbabel.to_smiles(data_str, input_format)
    else:
        sdf_data = avogadro.convert_str(data_str, input_format, 'sdf')
        smiles = openbabel.to_smiles(sdf_data, 'sdf')

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
        # Use sdf without 3d generation for avogadro's molecule properties
        sdf_no_3d = openbabel.gen_sdf_no_3d(smiles, smiles_format)[0]
        props = avogadro.molecule_properties(sdf_no_3d, 'sdf')

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

        if not cjson and using_2d_format:
            # Generate 3d coordinates in a background thread
            schedule_3d_coords_gen(mol_dict, user)
            # This will be complete other than the cjson
            return MoleculeModel().create(user, mol_dict, public)
        else:
            if input_format in openbabel_3d_formats:
                sdf_data = openbabel.convert_str(data_str, input_format, 'sdf')
                cjson = json.loads(avogadro.convert_str(sdf_data, 'sdf',
                                                        'cjson'))
            else:
                cjson = json.loads(avogadro.convert_str(data_str, input_format,
                                                        'cjson'))

        mol_dict['cjson'] = whitelist_cjson(cjson)

        mol = MoleculeModel().create(user, mol_dict, public)

        # Upload the molecule to virtuoso
        try:
            semantic.upload_molecule(mol)
        except requests.ConnectionError:
            print(TerminalColor.warning('WARNING: Couldn\'t connect to Jena.'))

    return mol
