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

from pytest_girder.assertions import assertStatusOk

from . import molecule

@pytest.mark.plugin('molecules')
def test_create_molecule(server, user):
    from girder.plugins.molecules.models.molecule import Molecule
    from girder.constants import AccessType

    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(dir_path + '/data/ethane.xyz', 'r') as rf:
        xyzData = rf.read()

    body = {
      'name': 'ethane',
      'xyz': xyzData
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

    # Find the molecule by name
    params = { 'name': name }
    r = server.request('/molecules', method='GET', params=params, user=user)
    assertStatusOk(r)

    # There should be exactly one
    assert len(r.json) == 1
    mol = r.json[0]

    assert mol.get('id') == _id
    assert mol.get('inchikey') == inchikey
    assert mol.get('name') == name

    # Find the molecule by inchi
    params = { 'inchi': inchi }
    r = server.request('/molecules', method='GET', params=params, user=user)
    assertStatusOk(r)

    # There should be exactly one
    assert len(r.json) == 1
    mol = r.json[0]

    assert mol.get('id') == _id
    assert mol.get('inchikey') == inchikey
    assert mol.get('name') == name

    # Find the molecule by inchikey
    params = { 'inchikey': inchikey }
    r = server.request('/molecules', method='GET', params=params, user=user)
    assertStatusOk(r)

    # There should be exactly one
    assert len(r.json) == 1
    mol = r.json[0]

    assert mol.get('id') == _id
    assert mol.get('inchikey') == inchikey
    assert mol.get('name') == name
