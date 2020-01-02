from openbabel import OBMol, OBConversion, pybel

import re

inchi_validator = re.compile('InChI=[0-9]S?\\/')


# This function only validates the first part. It does not guarantee
# that the entire InChI is valid.
def validate_start_of_inchi(inchi):
    if not inchi_validator.match(inchi):
        raise Exception('Invalid InChI: "' + inchi + '"')


# gen3d should be true for 2D input formats such as inchi or smiles
def convert_str(str_data, in_format, out_format, gen3d=False,
                add_hydrogens=False, perceive_bonds=False, out_options=None):

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

    if add_hydrogens:
        obMol.AddHydrogens()

    if gen3d:
        # Generate 3D coordinates for the input
        mol = pybel.Molecule(obMol)
        mol.make3D()

    if perceive_bonds:
        obMol.ConnectTheDots()
        obMol.PerceiveBondOrders()

    for option, value in out_options.items():
        conv.AddOption(option, conv.OUTOPTIONS, value)

    return (conv.WriteString(obMol), conv.GetOutFormat().GetMIMEType())


def to_inchi(str_data, in_format):
    mol = OBMol()
    conv = OBConversion()
    conv.SetInFormat(in_format)
    conv.ReadString(mol, str_data)

    conv.SetOutFormat('inchi')
    inchi = conv.WriteString(mol).rstrip()
    conv.SetOptions('K', conv.OUTOPTIONS)
    inchikey = conv.WriteString(mol).rstrip()

    return (inchi, inchikey)


def to_smiles(str_data, in_format):
    # The smiles has returns at the end of it, and may contain
    # a return in the middle with a common name. Get rid of
    # all of these.
    # Use canonical smiles
    smiles, mime = convert_str(str_data, in_format, 'can')
    smiles = smiles.strip().split()[0]
    return (smiles, mime)


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


def properties(str_data, in_format, add_hydrogens=False):
    # Returns a dict with the atom count, formula, heavy atom count,
    # mass, and spaced formula.
    if in_format == 'inchi' and not str_data.startswith('InChI='):
        # Inchi must start with 'InChI='
        str_data = 'InChI=' + str_data
        validate_start_of_inchi(str_data)
    mol = OBMol()
    conv = OBConversion()
    conv.SetInFormat(in_format)
    conv.ReadString(mol, str_data)

    if add_hydrogens:
        mol.AddHydrogens()

    props = {}
    props['atomCount'] = mol.NumAtoms()
    props['formula'] = mol.GetFormula()
    props['heavyAtomCount'] = mol.NumHvyAtoms()
    props['mass'] = mol.GetMolWt()
    props['spacedFormula'] = mol.GetSpacedFormula()

    return props


def to_svg(str_data, in_format):
    out_options = {
        'b': 'none',  # transparent background color
        'B': 'black'  # black bonds color
    }
    return convert_str(str_data, in_format, 'svg', out_options=out_options)
