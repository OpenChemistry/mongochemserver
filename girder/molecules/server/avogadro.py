from avogadro.core import *
from avogadro.io import *
import json
from jsonpath_rw import parse

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

# We expect JSON input here, using the NWChem format
def calculation_properties(json_data):
    properties = {}
    if not 'simulation' in json_data:
        return properties
    calcs = json_data['simulation']['calculations']
    if not isinstance(calcs, list) or len(calcs) == 0:
        return properties
    firstCalc = calcs[0]
    waveFunctionTypes = {
        'Density Functional Theory': 'DFT',
        'Hartree-Fock': 'HF' }
    if 'calculationSetup' in firstCalc:
        setup = firstCalc['calculationSetup']
        # Use a lookup, probably needs to be extended to cover all types...
        properties['theory'] = waveFunctionTypes[setup['waveFunctionTheory']].lower()
        properties['type'] = setup['waveFunctionType']

        calcName = properties['theory'] + ' (' + properties['type']
        if 'exchangeCorrelationFunctional' in setup:
            for piece in setup['exchangeCorrelationFunctional']:
                if 'xcName' in piece:
                     properties['functional'] = piece['xcName']
                     calcName += ' - ' + properties['functional']
        calcName += ')'
        properties['friendlyName'] = calcName

        if 'molecularCharge' in setup:
            properties['charge'] = setup['molecularCharge']
        if 'numberOfElectrons' in setup:
            properties['electronCount'] = setup['numberOfElectrons']
        if 'molecularSpinMultiplicity' in setup:
            properties['spin'] = setup['molecularSpinMultiplicity']

    if 'simulationEnvironment' in json_data['simulation']:
        env = json_data['simulation']['simulationEnvironment']
        properties['code'] = env['programRun']
        properties['codeVersion'] = env['programVersion']
        properties['processorCount'] = env['processorCount']
        properties['runDate'] = env['runDate']

    calcTypes = {
        'energyCalculation': 'energy',
        'geometryOptimization': 'optimization',
        'vibrationalModes': 'vibrational',
        'molecularProperties': 'properties' }
    calculationTypes = []
    calculations = []
    for calc in calcs:
        if 'calculationType' in calc:
            calculationTypes.append(calcTypes[calc['calculationType']])
            calc_obj = {
                'type': calcTypes[calc['calculationType']]
            }
            total_energy = parse('calculationResults.totalEnergy').find(calc)
            if total_energy:
                calc_obj['totalEnergy'] = total_energy[0].value

            zero_point_energy = \
                parse('calculationResults.zeroPointEnergyCorrection').find(calc)
            if zero_point_energy:
                calc_obj['zeroPointEnergyCorrection'] = \
                    zero_point_energy[0].value

            calculations.append(calc_obj)

    properties['calculationTypes'] = calculationTypes
    properties['calculations'] = calculations

    return properties

# This is far from ideal as it is a CPU intensive task blocking the main thread.
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
    cube.setLimits(mol, spacing, 4)
    gaussian = GaussianSetTools(mol)
    gaussian.calculateMolecularOrbital(cube, mo)

    return json.loads(conv.write_string(mol, "cjson"))
