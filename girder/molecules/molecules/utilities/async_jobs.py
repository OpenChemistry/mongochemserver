import functools
import json
import requests

from requests_futures.sessions import FuturesSession

from girder.constants import TerminalColor
from girder.models.model_base import ValidationException

from .whitelist_cjson import whitelist_cjson

from molecules.openbabel_api import openbabel_base_url

from .. import avogadro
from .. import semantic

from ..models.molecule import Molecule as MoleculeModel


def schedule_svg_gen(mol, user):
    mol['generating_svg'] = True

    base_url = openbabel_base_url()
    path = 'convert'
    output_format = 'svg'

    url = '/'.join([base_url, path, output_format])

    data = {
        'format': 'smi',
        'data': mol['smiles']
    }

    session = FuturesSession()
    future = session.post(url, json=data)

    inchikey = mol['inchikey']
    future.add_done_callback(functools.partial(_finish_svg_gen,
                                               inchikey, user))


def _finish_svg_gen(inchikey, user, future):

    resp = future.result()

    query = {
        'inchikey': inchikey
    }

    updates = {}
    updates.setdefault('$unset', {})['generating_svg'] = ''

    if resp.status_code == 200:
        updates.setdefault('$set', {})['svg'] = resp.text
    else:
        print('Generating SVG failed!')
        print('Status code was:', resp.status_code)
        print('Reason was:', resp.reason)

    update_result = super(MoleculeModel,
                          MoleculeModel()).update(query, updates)

    if update_result.matched_count == 0:
        raise ValidationException('Invalid inchikey (%s)' % inchikey)


def schedule_3d_coords_gen(mol, user):
    mol['generating_3d_coords'] = True

    base_url = openbabel_base_url()
    path = 'convert'
    output_format = 'sdf'

    url = '/'.join([base_url, path, output_format])

    data = {
        'format': 'smi',
        'data': mol['smiles'],
        'gen3d': True
    }

    session = FuturesSession()
    future = session.post(url, json=data)

    inchikey = mol['inchikey']
    future.add_done_callback(functools.partial(_finish_3d_coords_gen,
                                               inchikey, user))


def _finish_3d_coords_gen(inchikey, user, future):

    resp = future.result()

    query = {
        'inchikey': inchikey
    }

    updates = {}
    updates.setdefault('$unset', {})['generating_3d_coords'] = ''

    if resp.status_code == 200:
        sdf_data = resp.text
        cjson = json.loads(avogadro.convert_str(sdf_data, 'sdf',
                                                'cjson'))
        cjson = whitelist_cjson(cjson)
        updates.setdefault('$set', {})['cjson'] = cjson
    else:
        print('Generating SDF failed!')
        print('Status code was:', resp.status_code)
        print('Reason was:', resp.reason)

    update_result = super(MoleculeModel,
                          MoleculeModel()).update(query, updates)

    if update_result.matched_count == 0:
        raise ValidationException('Invalid inchikey (%s)' % inchikey)

    # Upload the molecule to virtuoso
    try:
        semantic.upload_molecule(MoleculeModel().findOne(query))
    except requests.ConnectionError:
        print(TerminalColor.warning('WARNING: Couldn\'t connect to Jena.'))
