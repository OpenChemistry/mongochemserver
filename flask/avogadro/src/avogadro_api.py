from avogadro.core import Molecule, GaussianSetTools
from avogadro.io import FileFormatManager
import json


def calculate_mo(cjson, mo):
    mol = Molecule()
    conv = FileFormatManager()
    conv.read_string(mol, json.dumps(cjson), 'cjson')
    # Do some scaling of our spacing based on the size of the molecule.
    atom_count = mol.atom_count()
    spacing = 0.30
    if atom_count > 50:
        spacing = 0.5
    elif atom_count > 30:
        spacing = 0.4
    elif atom_count > 10:
        spacing = 0.33
    cube = mol.add_cube()
    # Hard wiring spacing/padding for now, this could be exposed in future too.
    cube.set_limits(mol, spacing, 4)
    gaussian = GaussianSetTools(mol)
    gaussian.calculate_molecular_orbital(cube, mo)

    return conv.write_string(mol, "cjson")


def convert_str(str_data, in_format, out_format):
    mol = Molecule()
    conv = FileFormatManager()
    conv.read_string(mol, str_data, in_format)

    return conv.write_string(mol, out_format)


def atom_count(str_data, in_format):
    mol = Molecule()
    conv = FileFormatManager()
    conv.read_string(mol, str_data, in_format)

    return mol.atom_count()


def molecule_properties(str_data, in_format):
    mol = Molecule()
    conv = FileFormatManager()
    conv.read_string(mol, str_data, in_format)
    properties = {
        'atomCount': mol.atom_count(),
        'heavyAtomCount': mol.atom_count() - mol.atom_count(1),
        'mass': mol.mass(),
        'spacedFormula': mol.formula(' ', 0),
        'formula': mol.formula('', 1)
        }
    return properties
