#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright 2018 Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import json
import os
import pytest

from pytest_girder.assertions import assertStatusOk, assertStatus


@pytest.mark.plugin('molecules')
def test_create_molecule_xyz(server, user):
    from molecules.models.molecule import Molecule
    from girder.constants import AccessType

    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(dir_path + '/data/ethane.xyz', 'r') as rf:
        xyz_data = rf.read()

    body = {
        'name': 'ethane',
        'xyz': xyz_data
    }

    r = server.request('/molecules', method='POST', type='application/json',
                       body=json.dumps(body), user=user)
    assertStatusOk(r)

    mol = r.json
    assert '_id' in mol
    assert 'inchi' in mol
    assert 'inchikey' in mol

    # Double check and make sure it exists
    id = mol['_id']
    mol2 = Molecule().load(id, level=AccessType.READ, user=user)

    assert '_id' in mol2
    assert 'inchi' in mol2
    assert 'inchikey' in mol2

    # id, inchi, and inchikey should match
    assert str(mol['_id']) == str(mol2['_id'])
    assert mol['inchi'] == mol2['inchi']
    assert mol['inchikey'] == mol2['inchikey']

    # Delete the molecule
    r = server.request('/molecules/%s' % id, method='DELETE', user=user)
    assertStatusOk(r)


@pytest.mark.plugin('molecules')
def test_create_molecule_file_id(server, user, fsAssetstore, make_girder_file):
    from molecules.models.molecule import Molecule
    from girder.constants import AccessType

    dir_path = os.path.dirname(os.path.realpath(__file__))

    test_file = 'ethane.xyz'
    with open(dir_path + '/data/' + test_file, 'r') as rf:
        girder_file = make_girder_file(fsAssetstore, user, test_file,
                                       contents=rf.read().encode('utf-8'))

    assert '_id' in girder_file
    file_id = str(girder_file['_id'])

    body = {
        'fileId': file_id,
    }

    r = server.request('/molecules', method='POST', type='application/json',
                       body=json.dumps(body), user=user)
    assertStatusOk(r)

    mol = r.json
    assert '_id' in mol
    assert 'inchi' in mol
    assert 'inchikey' in mol
    assert 'properties' in mol
    assert 'formula' in mol['properties']
    assert mol['properties']['formula'] == 'C2H6'

    # Double check and make sure it exists
    id = mol['_id']
    mol2 = Molecule().load(id, level=AccessType.READ, user=user)

    assert '_id' in mol2
    assert 'inchi' in mol2
    assert 'inchikey' in mol2
    assert 'properties' in mol
    assert 'formula' in mol['properties']
    assert mol['properties']['formula'] == 'C2H6'

    # id, inchi, and inchikey should match
    assert str(mol['_id']) == str(mol2['_id'])
    assert mol['inchi'] == mol2['inchi']
    assert mol['inchikey'] == mol2['inchikey']

    # Delete the molecule
    r = server.request('/molecules/%s' % id, method='DELETE', user=user)
    assertStatusOk(r)


@pytest.mark.plugin('molecules')
def test_create_molecule_inchi(server, user):
    from molecules.models.molecule import Molecule
    from girder.constants import AccessType

    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(dir_path + '/data/water.inchi', 'r') as rf:
        inchi_data = rf.read()

    body = {
        'name': 'water',
        'inchi': inchi_data
    }

    r = server.request('/molecules', method='POST', type='application/json',
                       body=json.dumps(body), user=user)
    assertStatusOk(r)

    mol = r.json
    assert '_id' in mol
    assert 'inchi' in mol
    assert 'inchikey' in mol
    assert 'properties' in mol
    assert 'formula' in mol['properties']
    assert mol['properties']['formula'] == 'H2O'

    # Double check and make sure it exists
    id = mol['_id']
    mol2 = Molecule().load(id, level=AccessType.READ, user=user)

    assert '_id' in mol2
    assert 'inchi' in mol2
    assert 'inchikey' in mol2
    assert 'properties' in mol
    assert 'formula' in mol['properties']
    assert mol['properties']['formula'] == 'H2O'

    # id, inchi, and inchikey should match
    assert str(mol['_id']) == str(mol2['_id'])
    assert mol['inchi'] == mol2['inchi']
    assert mol['inchikey'] == mol2['inchikey']

    # Delete the molecule
    r = server.request('/molecules/%s' % id, method='DELETE', user=user)
    assertStatusOk(r)


@pytest.mark.plugin('molecules')
def test_create_molecule_smiles(server, user):
    from molecules.models.molecule import Molecule
    from girder.constants import AccessType

    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(dir_path + '/data/water.smi', 'r') as rf:
        smi_data = rf.read()

    body = {
        'name': 'water',
        'smi': smi_data
    }

    r = server.request('/molecules', method='POST', type='application/json',
                       body=json.dumps(body), user=user)
    assertStatusOk(r)

    mol = r.json
    assert '_id' in mol
    assert 'inchi' in mol
    assert 'inchikey' in mol
    assert 'properties' in mol
    assert 'formula' in mol['properties']
    assert mol['properties']['formula'] == 'H2O'

    # Double check and make sure it exists
    id = mol['_id']
    mol2 = Molecule().load(id, level=AccessType.READ, user=user)

    assert '_id' in mol2
    assert 'inchi' in mol2
    assert 'inchikey' in mol2
    assert 'properties' in mol
    assert 'formula' in mol['properties']
    assert mol['properties']['formula'] == 'H2O'

    # id, inchi, and inchikey should match
    assert str(mol['_id']) == str(mol2['_id'])
    assert mol['inchi'] == mol2['inchi']
    assert mol['inchikey'] == mol2['inchikey']

    # Delete the molecule
    r = server.request('/molecules/%s' % id, method='DELETE', user=user)
    assertStatusOk(r)


@pytest.mark.plugin('molecules')
def test_get_molecule(server, molecule, user):

    # The molecule will have been created by the fixture
    assert '_id' in molecule
    assert 'inchi' in molecule
    assert 'inchikey' in molecule

    # This one is not essential, but we set it ourselves
    assert 'name' in molecule

    _id = molecule['_id']
    inchi = molecule['inchi']
    inchikey = molecule['inchikey']
    name = molecule['name']
    properties = molecule['properties']

    # Find all molecules (no query parameters)
    params = {}
    r = server.request('/molecules', method='GET', params=params, user=user)
    assertStatusOk(r)

    # There should be exactly one
    assert len(r.json) == 1
    mol = r.json[0]

    assert mol.get('_id') == _id
    assert mol.get('inchikey') == inchikey
    assert mol.get('name') == name
    assert mol.get('properties') == properties


    # Find the molecule by name
    params = {'name': name}
    r = server.request('/molecules', method='GET', params=params, user=user)
    assertStatusOk(r)

    # There should be exactly one
    assert len(r.json) == 1
    mol = r.json[0]

    assert mol.get('_id') == _id
    assert mol.get('inchikey') == inchikey
    assert mol.get('name') == name
    assert mol.get('properties') == properties

    # Find the molecule by inchi
    params = {'inchi': inchi}
    r = server.request('/molecules', method='GET', params=params, user=user)
    assertStatusOk(r)

    # There should be exactly one
    assert len(r.json) == 1
    mol = r.json[0]

    assert mol.get('_id') == _id
    assert mol.get('inchikey') == inchikey
    assert mol.get('name') == name
    assert mol.get('properties') == properties

    # Find the molecule by inchikey
    params = {'inchikey': inchikey}
    r = server.request('/molecules', method='GET', params=params, user=user)
    assertStatusOk(r)

    # There should be exactly one
    assert len(r.json) == 1
    mol = r.json[0]

    assert mol.get('_id') == _id
    assert mol.get('inchikey') == inchikey
    assert mol.get('name') == name
    assert mol.get('properties') == properties

    # Get molecule by id
    params = {}
    r = server.request('/molecules/%s' % _id, method='GET', params=params, user=user)
    assertStatusOk(r)

    # The molecule document is returned
    mol = r.json

    assert mol.get('_id') == _id
    assert mol.get('inchikey') == inchikey
    assert mol.get('name') == name
    assert mol.get('properties') == properties
    assert mol.get('cjson') is not None

    # Get molecule by id
    params = {'cjson': 'false'}
    r = server.request('/molecules/%s' % _id, method='GET', params=params, user=user)
    assertStatusOk(r)

    # The molecule document is returned
    mol = r.json

    assert mol.get('_id') == _id
    assert mol.get('inchikey') == inchikey
    assert mol.get('name') == name
    assert mol.get('properties') == properties
    assert mol.get('cjson') is None


@pytest.mark.plugin('molecules')
def test_get_molecule_inchikey(server, molecule, user):

    # The molecule will have been created by the fixture
    assert '_id' in molecule
    assert 'inchi' in molecule
    assert 'inchikey' in molecule

    # This one is not essential, but we set it ourselves
    assert 'name' in molecule

    _id = molecule['_id']
    inchi = molecule['inchi']
    inchikey = molecule['inchikey']
    name = molecule['name']

    # Find the molecule by its inchikey
    r = server.request('/molecules/inchikey/%s' % inchikey, method='GET',
                       user=user)
    assertStatusOk(r)

    mol = r.json

    assert mol.get('_id') == _id
    assert mol.get('inchi') == inchi
    assert mol.get('inchikey') == inchikey
    assert mol.get('name') == name


@pytest.mark.plugin('molecules')
def test_search_molecule_formula(server, molecule, user):

    # The molecule will have been created by the fixture
    assert '_id' in molecule
    assert 'inchi' in molecule
    assert 'inchikey' in molecule
    assert 'properties' in molecule
    assert 'formula' in molecule['properties']

    # This one is not essential, but we set it ourselves
    assert 'name' in molecule

    _id = molecule['_id']
    inchi = molecule['inchi']
    inchikey = molecule['inchikey']
    name = molecule['name']
    formula = molecule['properties']['formula']

    ethane_formula = 'C2H6'
    assert formula == ethane_formula

    # Find the molecule by its formula. Formula here is C2H6.
    params = {'formula': ethane_formula}
    r = server.request('/molecules/search', method='GET', user=user,
                       params=params)
    assertStatusOk(r)

    # Should just be one
    assert len(r.json) == 1
    mol = r.json[0]

    # Everything should match
    assert mol.get('_id') == _id
    assert mol.get('inchi') == inchi
    assert mol.get('inchikey') == inchikey
    assert mol.get('name') == name
    assert mol.get('properties').get('formula') == ethane_formula
