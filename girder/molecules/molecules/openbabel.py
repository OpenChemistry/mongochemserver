import json
import requests

from girder.models.setting import Setting

from molecules.avogadro import convert_str as avo_convert_str
from molecules.constants import PluginSettings
from molecules.utilities.has_3d_coords import cjson_has_3d_coords

def openbabel_base_url():
    base_url = Setting().get(PluginSettings.OPENBABEL_BASE_URL)
    if base_url is None:
        base_url = 'http://localhost:5000'

    return base_url


def convert_str(data_str, input_format, output_format, extra_options=None):

    if extra_options is None:
        extra_options = {}

    base_url = openbabel_base_url()
    path = 'convert'
    url = '/'.join([base_url, path, output_format])

    data = {
        'format': input_format,
        'data': data_str,
    }
    data.update(extra_options)

    r = requests.post(url, json=data)

    if r.headers and 'content-type' in r.headers:
        mimetype = r.headers['content-type']
    else:
        mimetype = None

    return r.text, mimetype


def to_inchi(data_str, input_format):

    result, mime = convert_str(data_str, input_format, 'inchi')
    result = json.loads(result)

    return result.get('inchi'), result.get('inchikey')


def to_smiles(data_str, input_format):

    result, mime = convert_str(data_str, input_format, 'smi')
    return result


def gen_sdf_no_3d(data_str, input_format, add_hydrogens=True):

    extra_options = {
        'addHydrogens': add_hydrogens
    }

    return convert_str(data_str, input_format, 'sdf', extra_options)


def properties(data_str, input_format, add_hydrogens=True):

    base_url = openbabel_base_url()
    path = 'properties'
    url = '/'.join([base_url, path])

    data = {
        'format': input_format,
        'data': data_str,
        'addHydrogens': add_hydrogens
    }

    r = requests.post(url, json=data)

    return r.json()


def autodetect_bonds(cjson):
    # This function drops all bonding info and autodetects bonds
    # using Open Babel.

    # Only autodetect bonds if we have 3D coordinates
    if not cjson_has_3d_coords(cjson):
        return cjson

    cjson_str = json.dumps(cjson)
    xyz_str = avo_convert_str(cjson_str, 'cjson', 'xyz')

    extra_options = {
        'perceiveBonds': True
    }
    sdf_str, mime = convert_str(xyz_str, 'xyz', 'sdf', extra_options)

    cjson_str = avo_convert_str(sdf_str, 'sdf', 'cjson')
    return json.loads(cjson_str)
