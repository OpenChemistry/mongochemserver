import json
import requests

from .. import avogadro
from .. import openbabel
from .. import chemspider
from .. import semantic
from .. import constants
from molecules.models.molecule import Molecule as MoleculeModel
from girder.constants import TerminalColor
from girder.api.rest import RestException

from .async_requests import schedule_3d_coords_gen, schedule_svg_gen
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


def create_molecule(data_str, input_format, user, public, gen3d=True,
                    provenance='uploaded by user'):

    using_2d_format = (input_format in openbabel_2d_formats)
    inchi_format = 'inchi'

    if using_2d_format or input_format in openbabel_3d_formats:
        inchi, inchikey = openbabel.to_inchi(data_str, input_format)
    else:
        sdf_data = avogadro.convert_str(data_str, input_format, 'sdf')
        inchi, inchikey = openbabel.to_inchi(sdf_data, 'sdf')

    if not inchi:
        raise RestException('Unable to extract InChI', code=400)

    # Check if the molecule exists, only create it if it does.
    molExists = MoleculeModel().find_inchikey(inchikey)
    mol = {}
    if molExists:
        mol = molExists
    else:
        # Get some basic molecular properties we want to add to the
        # database.
        # Use sdf without 3d generation for avogadro's molecule properties
        sdf_no_3d = openbabel.gen_sdf_no_3d(inchi, inchi_format)[0]
        props = avogadro.molecule_properties(sdf_no_3d, 'sdf')
        smiles = openbabel.to_smiles(inchi, inchi_format)

        pieces = props['spacedFormula'].strip().split(' ')
        atomCounts = {}
        for i in range(0, int(len(pieces) / 2)):
            atomCounts[pieces[2 * i]] = int(pieces[2 * i + 1])

        mol_dict = {
            'inchi': inchi,
            'inchikey': inchikey,
            'smiles': smiles,
            'properties': props,
            'atomCounts': atomCounts,
            'provenance': provenance
        }

        # Generate an svg file for an image
        schedule_svg_gen(mol_dict, user)

        # Set a name if we find one
        name = chemspider.find_common_name(inchikey)
        if name is not None:
            mol_dict['name'] = name

        cjson = {}
        if input_format == 'cjson':
            cjson = json.loads(data_str)

        if not cjson and using_2d_format:
            # Generate 3d coordinates in a background thread
            if gen3d:
                schedule_3d_coords_gen(mol_dict, user)
            # This will be complete other than the cjson
            return MoleculeModel().create(user, mol_dict, public)
        else:
            if input_format in openbabel_3d_formats:
                sdf_data, mime = openbabel.convert_str(data_str, input_format,
                                                       'sdf')
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
