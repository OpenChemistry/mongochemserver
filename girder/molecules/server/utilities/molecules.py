import json
import requests

from girder.api.rest import RestException
from girder.api import access
from girder.constants import AccessType
from .. import avogadro
from .. import openbabel
from .. import chemspider
from .. import semantic
from .. import constants
from girder.plugins.molecules.models.molecule import Molecule as MoleculeModel
from girder.constants import TerminalColor


def create_molecule(data_str, input_format, user, public):
    # Use the SDF format as it is the one with bonding that 3Dmol uses.
    sdf_format = 'sdf'

    if input_format == 'pdb':
        (sdf_data, _) = openbabel.convert_str(data_str, input_format, sdf_format)
    elif input_format == 'inchi':
        (sdf_data, _) = openbabel.from_inchi(data_str, sdf_format)
    elif input_format == 'smi' or input_format == 'smiles':
        (sdf_data, _) = openbabel.from_smiles(data_str, sdf_format)
    else:
        sdf_data = avogadro.convert_str(data_str, input_format, sdf_format)

    atom_count = openbabel.atom_count(sdf_data, sdf_format)

    if atom_count > 1024:
        raise RestException('Unable to generate inchi, molecule has more than 1024 atoms .', code=400)

    (inchi, inchikey) = openbabel.to_inchi(sdf_data, sdf_format)

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
        props = avogadro.molecule_properties(sdf_data, sdf_format)
        pieces = props['spacedFormula'].strip().split(' ')
        atomCounts = {}
        for i in range(0, int(len(pieces) / 2)):
            atomCounts[pieces[2 * i ]] = int(pieces[2 * i + 1])

        cjson = {}
        if input_format == 'cjson':
            cjson = json.loads(data_str)
        else:
            cjson = json.loads(avogadro.convert_str(sdf_data, sdf_format,
                                                    'cjson'))

        smiles = openbabel.to_smiles(sdf_data, sdf_format)

        # Whitelist parts of the CJSON that we store at the top level.
        cjsonmol = {}
        cjsonmol['atoms'] = cjson['atoms']
        cjsonmol['bonds'] = cjson['bonds']
        cjsonmol['chemicalJson'] = cjson['chemicalJson']
        mol_dict = {
            'name': chemspider.find_common_name(inchikey, props['formula']),
            'inchi': inchi,
            'inchikey': inchikey,
            'smiles': smiles,
            sdf_format: sdf_data,
            'cjson': cjsonmol,
            'properties': props,
            'atomCounts': atomCounts
        }
        mol = MoleculeModel().create(user, mol_dict, public)

        # Upload the molecule to virtuoso
        try:
            semantic.upload_molecule(mol)
        except requests.ConnectionError:
            print(TerminalColor.warning('WARNING: Couldn\'t connect to virtuoso.'))

    return mol
