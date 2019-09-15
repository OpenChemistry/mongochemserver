from avogadro.core import *
from avogadro.io import *
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