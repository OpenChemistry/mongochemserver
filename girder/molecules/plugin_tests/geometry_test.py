#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright 2019 Kitware Inc.
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


@pytest.mark.plugin('molecules')
def test_create_geometry(server, molecule, user):

    # The molecule will have been created by the fixture
    assert '_id' in molecule

    _id = molecule['_id']

    # Get some cjson
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(dir_path + '/data/ethane.cjson', 'r') as rf:
        ethane_cjson = json.load(rf)

    # Whitelist the cjson to only contain the parts needed for geometry
    whitelist = ['atoms', 'bonds', 'chemical json']
    cjson = {}
    for item in whitelist:
        cjson[item] = ethane_cjson[item]

    # Create a geometry
    params = {
        'moleculeId': _id,
        'cjson': json.dumps(cjson)
    }
    r = server.request('/geometry', method='POST', params=params, user=user)
    assertStatusOk(r)

    output = r.json

    assert '_id' in output
    assert 'moleculeId' in output and output['moleculeId'] == _id
    assert 'cjson' in output and output['cjson'] == cjson
    assert 'provenanceType' in output and output['provenanceType'] == 'user'
    assert 'provenanceId' in output and len(output['provenanceId']) > 0

    id = output['_id']

    # Delete the geometry
    r = server.request('/geometry/%s' % id, method='DELETE', user=user)
    assertStatusOk(r)


@pytest.mark.plugin('molecules')
def test_get_geometry(server, geometry, user):

    # The geometry will have been created by the fixture
    assert '_id' in geometry
    assert 'moleculeId' in geometry
    assert 'cjson' in geometry

    # These are not essential, but we set it ourselves
    assert 'provenanceType' in geometry
    assert 'provenanceId' in geometry

    _id = geometry['_id']
    molecule_id = geometry['moleculeId']
    cjson = geometry['cjson']
    provenance_type = geometry['provenanceType']
    provenance_id = geometry['provenanceId']

    # Find the geometry by its parent molecule.
    params = {'moleculeId': molecule_id}
    r = server.request('/geometry', method='GET', user=user,
                       params=params)
    assertStatusOk(r)

    # Should just be one
    assert len(r.json) == 1
    geometry = r.json[0]

    # Everything should match
    assert geometry.get('_id') == str(_id)
    assert geometry.get('moleculeId') == str(molecule_id)
    assert geometry.get('cjson') == cjson
    assert geometry.get('provenanceType') == provenance_type
    assert geometry.get('provenanceId') == str(provenance_id)
