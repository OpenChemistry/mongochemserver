import functools
import json
import requests
import datetime

import openchemistry as oc

from requests_futures.sessions import FuturesSession

from girder.api.rest import getCurrentUser
from girder.constants import TerminalColor
from girder.models.notification import Notification
from girder.models.model_base import ValidationException
from girder.utility.model_importer import ModelImporter

from .whitelist_cjson import whitelist_cjson

from molecules.openbabel import openbabel_base_url

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

def schedule_orbital_gen(cjson, mo, id, orig_mo):
    cjson['generating_orbital'] = True

    url = 'http://avogadro:5000/calculate'
    data = {
        'cjson': cjson,
        'mo': mo,
    }

    session = FuturesSession()
    future = session.post(url, json=data)

    future.add_done_callback(functools.partial(_finish_orbital_gen, mo, id, getCurrentUser(), orig_mo))

def _finish_orbital_gen(mo, id, user, orig_mo, future):
    resp = future.result()
    cjson = json.loads(resp.text)
    
    if 'vibrations' in cjson:
        del cjson['vibrations']

    # Add cube to cache
    ModelImporter.model('cubecache', 'molecules').create(id, mo, cjson)
    
    # #Create notification to indicate cube can be retrieved now
    data = {'id':id, 'mo':orig_mo}
    Notification().createNotification(type='cube.status', data=data, user=user, expires=datetime.datetime.utcnow() + datetime.timedelta(seconds=30))
