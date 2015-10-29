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
        'heavyAtomCount': mol.atomCount() - mol.atomCount(1),
        'mass': mol.mass(),
        'spacedFormula': mol.formula(' ', 0),
        'formula': mol.formula('', 1)
        }
    return properties
