import json
import requests

from avogadro.core import Molecule
from avogadro.io import FileFormatManager

from girder.models.setting import Setting

from jsonpath_rw import parse

from molecules.constants import PluginSettings


def avogadro_base_url():
    base_url = Setting().get(PluginSettings.AVOGADRO_BASE_URL)
    if base_url is None:
        base_url = 'http://localhost:5001'

    return base_url


def convert_str(str_data, in_format, out_format):
    mol = Molecule()
    conv = FileFormatManager()
    conv.read_string(mol, str_data, in_format)

    return conv.write_string(mol, out_format)


def atom_count(str_data, in_format):
    base_url = avogadro_base_url()
    path = 'properties'
    url = '/'.join([base_url, path, 'atom'])

    data = {
        'format': in_format,
        'data': str_data,
    }

    r = requests.post(url, json=data)

    return int(r.text)


def molecule_properties(str_data, in_format):
    base_url = avogadro_base_url()
    path = 'properties'
    url = '/'.join([base_url, path, 'molecule'])

    data = {
        'format': in_format,
        'data': str_data,
    }

    r = requests.post(url, json=data)

    return r.text


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
        'Hartree-Fock': 'HF'}
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
        'molecularProperties': 'properties'}
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


def calculate_mo(cjson, mo):
    base_url = avogadro_base_url()
    path = 'calculate'
    url = '/'.join([base_url, path])

    data = {
        'cjson': cjson,
        'mo': mo,
    }

    r = requests.post(url, json=data)

    return json.loads(r.text)
