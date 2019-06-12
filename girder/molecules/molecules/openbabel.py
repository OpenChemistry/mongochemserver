from girder.api.rest import RestException

import json
from openbabel import OBMol, OBConversion

import pybel

import re

from .avogadro import convert_str as avo_convert_str

from .models.molecule import Molecule as MoleculeModel

inchi_validator = re.compile('InChI=[0-9]S?\/')

# This function only validates the first part. It does not guarantee
# that the entire InChI is valid.
def validate_start_of_inchi(inchi):
    if not inchi_validator.match(inchi):
        raise RestException('Invalid InChI: "' + inchi +'"', 400)

# gen3d should be true for 2D input formats such as inchi or smiles
def convert_str(str_data, in_format, out_format, gen3d=False, out_options=None):

    # Make sure that the start of InChI is valid before passing it to
    # Open Babel, or Open Babel will crash the server.
    if in_format.lower() == 'inchi':
        validate_start_of_inchi(str_data)

    if out_options is None:
        out_options = {}

    obMol = OBMol()
    conv = OBConversion()
    conv.SetInFormat(in_format)
    conv.SetOutFormat(out_format)
    conv.ReadString(obMol, str_data)

    if gen3d:
        # Generate 3D coordinates for the input
        mol = pybel.Molecule(obMol)
        mol.make3D()

    for option, value in out_options.items():
        conv.AddOption(option, conv.OUTOPTIONS, value)

    return (conv.WriteString(obMol), conv.GetOutFormat().GetMIMEType())

def gen_sdf_no_3d(str_data, in_format):

    obMol = OBMol()
    conv = OBConversion()
    conv.SetInFormat(in_format)
    conv.SetOutFormat('sdf')
    conv.ReadString(obMol, str_data)

    obMol.AddHydrogens()

    return (conv.WriteString(obMol), conv.GetOutFormat().GetMIMEType())

def cjson_to_ob_molecule(cjson):
    cjson_str = json.dumps(cjson)
    sdf_str = avo_convert_str(cjson_str, 'cjson', 'sdf')
    conv = OBConversion()
    conv.SetInFormat('sdf')
    conv.SetOutFormat('sdf')
    mol = OBMol()
    conv.ReadString(mol, sdf_str)
    return mol

def autodetect_bonds(cjson):
    # Only autodetect bonds if we have 3D coordinates
    if not MoleculeModel().cjson_has_3d_coords(cjson):
        return cjson

    mol = cjson_to_ob_molecule(cjson)
    mol.ConnectTheDots()
    mol.PerceiveBondOrders()
    conv = OBConversion()
    conv.SetInFormat('sdf')
    conv.SetOutFormat('sdf')
    sdf_str = conv.WriteString(mol)
    cjson_str = avo_convert_str(sdf_str, 'sdf', 'cjson')
    return json.loads(cjson_str)

def to_inchi(str_data, in_format):
    mol = OBMol()
    conv = OBConversion()
    conv.SetInFormat(in_format)
    # Hackish for now, convert to xyz first...
    conv.SetOutFormat('xyz')
    conv.ReadString(mol, str_data)
    xyz = conv.WriteString(mol)

    # Now convert to inchi and inchikey.
    mol = OBMol()
    conv.SetInFormat('xyz')
    conv.ReadString(mol, xyz)

    conv.SetOutFormat('inchi')
    inchi = conv.WriteString(mol).rstrip()
    conv.SetOptions("K", conv.OUTOPTIONS)
    inchikey = conv.WriteString(mol).rstrip()

    return (inchi, inchikey)

def from_inchi(str_data, out_format):
    return convert_str(str_data, 'inchi', out_format, True)

def to_smiles(str_data, in_format):
    # This returns ["<smiles>", "chemical/x-daylight-smiles"]
    # Keep only the first part.
    # The smiles has returns at the end of it, and may contain
    # a return in the middle with a common name. Get rid of
    # all of these.
    # Use canonical smiles
    smiles = convert_str(str_data, in_format, 'can')[0].strip()
    return smiles.split()[0]

def from_smiles(str_data, out_format):
    return convert_str(str_data, 'smi', out_format, True)

def atom_count(str_data, in_format):
    mol = OBMol()
    conv = OBConversion()
    conv.SetInFormat(in_format)
    conv.ReadString(mol, str_data)

    return mol.NumAtoms()

def get_formula(str_data, in_format):
    # Inchi must start with 'InChI='
    if in_format == 'inchi' and not str_data.startswith('InChI='):
        str_data = 'InChI=' + str_data
        validate_start_of_inchi(str_data)
    # Get the molecule using the "Hill Order" - i. e., C first, then H,
    # and then alphabetical.
    mol = OBMol()
    conv = OBConversion()
    conv.SetInFormat(in_format)
    conv.ReadString(mol, str_data)

    return mol.GetFormula()

def to_svg(str_data, in_format):
    out_options = {
        'b': 'none', # transparent background color
        'B': 'black' # black bonds color
    }
    return convert_str(str_data, in_format, 'svg', out_options=out_options)[0]
