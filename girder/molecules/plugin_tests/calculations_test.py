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
    params = {'moleculeId': calc_molecule_id}
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


@pytest.mark.plugin('molecules')
def test_put_properties(server, molecule, calculation, user):
    from girder.plugins.molecules.models.calculation import Calculation
    from girder.constants import AccessType

    assert '_id' in calculation
    assert 'moleculeId' in calculation
    assert 'properties' in calculation
    calc_id = str(calculation['_id'])
    calc_molecule_id = str(calculation['moleculeId'])
    calc_properties = calculation['properties']

    # We put these properties in ourselves
    assert 'molecular mass' in calc_properties
    assert 'boiling point' in calc_properties
    assert 'melting point' in calc_properties

    # Make sure these have the right values
    assert pytest.approx(calc_properties['molecular mass'], 1.e-4) == 30.0690
    assert calc_properties['melting point'] == -172
    assert calc_properties['boiling point'] == -88

    # Replace these properties with some new properties
    new_properties = {
        'critical temperature': 32.2,
        'critical pressure': 49.0
    }
    r = server.request('/calculations/%s/properties' % calc_id, method='PUT',
                       body=json.dumps(new_properties), user=user,
                       type='application/json')
    assertStatusOk(r)

    # Grab the new calculation
    updated_calc = Calculation().load(calc_id, level=AccessType.READ, user=user)

    # It should have an _id and a molecule id, and it should match
    assert '_id' in updated_calc
    assert 'moleculeId' in updated_calc
    assert 'properties' in updated_calc

    assert str(updated_calc['_id']) == calc_id
    assert str(updated_calc['moleculeId']) == calc_molecule_id

    # Make sure the old properties are no longer here
    updated_calc_properties = updated_calc['properties']
    assert 'molecular mass' not in updated_calc_properties
    assert 'boiling point' not in updated_calc_properties
    assert 'melting point' not in updated_calc_properties

    # The new properties should be here, though
    assert 'critical temperature' in updated_calc_properties
    assert 'critical pressure' in updated_calc_properties

    # Make sure these are correct also
    assert pytest.approx(
        updated_calc_properties['critical temperature'],
        1.e-1) == new_properties['critical temperature']
    assert pytest.approx(
        updated_calc_properties['critical pressure'],
        1.e-1) == new_properties['critical pressure']
