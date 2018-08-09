#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright 2018 Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the 'License' );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an 'AS IS' BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import json
import pytest
import os

from pytest_girder.assertions import assertStatusOk, assertStatus

from . import calculation
from . import molecule

@pytest.mark.plugin('molecules')
def test_create_calc(server, molecule, user):
    from girder.plugins.molecules.models.calculation import Calculation
    from girder.constants import AccessType

    assert '_id' in molecule

    dir_path = os.path.dirname(os.path.realpath(__file__))

    # This cjson should match the molecule
    with open(dir_path + '/data/ethane.cjson', 'r') as rf:
        ethane_cjson = rf.read()

    # Let's make some properties
    properties = {
        'molecular mass': 30.0690,
        'melting point': -172,
        'boiling point': -88
    }

    body = {
        'cjson': ethane_cjson,
        'properties': properties,
        'moleculeId': molecule['_id']
    }

    r = server.request('/calculations', method='POST', body=json.dumps(body),
                       type='application/json', user=user)
    assertStatus(r, 201)

    calc = r.json

    assert '_id' in calc
    assert 'moleculeId' in calc
    calc_id = str(calc['_id'])
    molecule_id = calc['moleculeId']

    calc2 = Calculation().load(calc_id, level=AccessType.READ, user=user)

    # It should have an _id and a molecule id, and it should match
    assert '_id' in calc2
    assert 'moleculeId' in calc2

    assert str(calc2['_id']) == calc_id
    assert str(calc2['moleculeId']) == molecule_id

@pytest.mark.plugin('molecules')
def test_get_calc(server, molecule, calculation, user):

    assert '_id' in calculation
    assert 'moleculeId' in calculation
    calc_id = str(calculation['_id'])
    calc_molecule_id = str(calculation['moleculeId'])

    # Find it by molecule id
    params = { 'moleculeId': calc_molecule_id }
    r = server.request('/calculations', method='GET', params=params, user=user)
    assertStatusOk(r)

    # Should just be one calculation
    assert len(r.json) == 1

    calc = r.json[0]

    assert '_id' in calc
    assert str(calc['_id']) == calc_id

    # Find it by its own id
    r = server.request('/calculations/%s' % calc_id, method='GET', user=user)
    assertStatusOk(r)

    calc = r.json

    assert '_id' in calc
    assert str(calc['_id']) == calc_id
