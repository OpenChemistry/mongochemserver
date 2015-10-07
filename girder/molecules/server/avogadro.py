from avogadro2 import Molecule, FileFormatManager

def convert_str(str_data, in_format, out_format):
    mol = Molecule()
    conv = FileFormatManager()
    conv.readString(mol, str_data, in_format)

    return conv.writeString(mol, out_format)

def atom_count(str_data, in_format):
    mol = Molecule()
    conv = FileFormatManager()
    conv.readString(mol, str_data, in_format)

    return mol.atomCount()