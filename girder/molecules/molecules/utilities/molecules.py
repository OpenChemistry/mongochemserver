import json
import requests

from jsonpath_rw import parse

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

openbabel_formats = openbabel_2d_formats + openbabel_3d_formats


def create_molecule(data_str, input_format, user, public, gen3d=True,
                    provenance='uploaded by user'):

    using_2d_format = (input_format in openbabel_2d_formats)
    inchi_format = 'inchi'

    if using_2d_format:
        inchi, inchikey = openbabel.to_inchi(data_str, input_format)
    else:
        # Let's make sure the bonds look reasonable
        cjson = convert_3d_format_to_cjson(data_str, input_format)
        if bonding_looks_suspicious(cjson):
            tmp = openbabel.autodetect_bonds(cjson)
            cjson['bonds'] = tmp['bonds']

        # Use this cjson for generating the inchi
        sdf_data = avogadro.convert_str(json.dumps(cjson), 'cjson', 'sdf')
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

        # Set a name if we find one
        name = chemspider.find_common_name(inchikey)
        if name is not None:
            mol_dict['name'] = name

        if not using_2d_format:
            # The cjson should already be a local variable
            mol_dict['cjson'] = whitelist_cjson(cjson)

        mol = MoleculeModel().create(user, mol_dict, public)

        if using_2d_format and gen3d:
            def _on_complete(mol):
                # Upload the molecule to Jen
                try:
                    semantic.upload_molecule(mol)
                except requests.ConnectionError:
                    print(TerminalColor.warning('WARNING: Couldn\'t connect to Jena.'))

            schedule_3d_coords_gen(mol_dict, user, on_complete=_on_complete)

        # Generate an svg file for an image
        schedule_svg_gen(mol_dict, user)

    return mol


def convert_3d_format_to_cjson(data_str, input_format):
    # This returns the cjson as a dictionary
    if input_format == 'cjson':
        return json.loads(data_str)

    if input_format in openbabel_3d_formats:
        data_str = openbabel.convert_str(data_str, input_format, 'sdf')
        input_format = 'sdf'

    cjson = avogadro.convert_str(data_str, input_format, 'cjson')
    return json.loads(cjson)


def bonding_looks_suspicious(cjson):
    # Right now, we consider bonding to look suspicious if there
    # are no bonds, or if there are only single bonds.
    orders = parse('bonds.order').find(cjson)
    if not orders or len(orders[0].value) == 0:
        return True

    return all(x == 1 for x in orders[0].value)
