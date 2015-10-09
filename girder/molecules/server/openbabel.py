from openbabel import OBMol, OBConversion

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
    # Hackish for now, convert to xyz, then
    conv.SetOutFormat('xyz')
    conv.ReadString(mol, str_data)
    xyz = conv.WriteString(mol)
    mol.Clear()
    conv.SetInFormat('xyz')
    conv.SetOutFormat('inchi')
    conv.ReadString(mol, xyz)
    inchi = conv.WriteString(mol).rstrip()
    conv.SetOptions("K", conv.OUTOPTIONS)
    inchikey = conv.WriteString(mol).rstrip()

    return (inchi, inchikey)

def atom_count(str_data, in_format):
    mol = OBMol()
    conv = OBConversion()
    conv.SetInFormat(in_format)
    conv.ReadString(mol, str_data)

    return mol.NumAtoms()