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

def molecule_properties(str_data, in_format):
    mol = Molecule()
    conv = FileFormatManager()
    conv.readString(mol, str_data, in_format)
    properties = {
        'atomCount': mol.atomCount(),
        'mass': mol.mass(),
        'formula': mol.formula('', 1),
        'spacedFormula': mol.formula(' ', 0)
        }
    return properties
