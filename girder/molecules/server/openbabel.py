from openbabel import OBMol, OBConversion

import pybel

def convert_str(str_data, in_format, out_format):
    mol = OBMol()
    conv = OBConversion()
    conv.SetInFormat(in_format)
    conv.SetOutFormat(out_format)
    conv.ReadString(mol, str_data)

    return (conv.WriteString(mol), conv.GetOutFormat().GetMIMEType())

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
    obMol = OBMol()
    conv = OBConversion()
    conv.SetInFormat('inchi')
    conv.SetOutFormat(out_format)
    conv.ReadString(obMol, str_data)

    # Generate 3D coordinates for the inchi
    mol = pybel.Molecule(obMol)
    mol.make3D()

    return (conv.WriteString(obMol), conv.GetOutFormat().GetMIMEType())

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
