from openbabel import OBMol, OBConversion

import pybel

# gen3d should be true for 2D input formats such as inchi or smiles
def convert_str(str_data, in_format, out_format, gen3d=False):
    obMol = OBMol()
    conv = OBConversion()
    conv.SetInFormat(in_format)
    conv.SetOutFormat(out_format)
    conv.ReadString(obMol, str_data)

    if gen3d:
        # Generate 3D coordinates for the input
        mol = pybel.Molecule(obMol)
        mol.make3D()

    return (conv.WriteString(obMol), conv.GetOutFormat().GetMIMEType())

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
    # Get the molecule using the "Hill Order" - i. e., C first, then H,
    # and then alphabetical.
    mol = OBMol()
    conv = OBConversion()
    conv.SetInFormat(in_format)
    conv.ReadString(mol, str_data)

    return mol.GetFormula()
