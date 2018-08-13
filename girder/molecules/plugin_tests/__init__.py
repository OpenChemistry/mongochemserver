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

import pytest
import os

# Our method for creating a molecule
@pytest.fixture
def molecule(user):
    from girder.plugins.molecules.models.molecule import Molecule
    from girder.plugins.molecules import openbabel

    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(dir_path + '/data/ethane.xyz', 'r') as rf:
        xyz_data = rf.read()

    input_format = 'xyz'
    data = xyz_data
    name = 'ethane'

    (inchi, inchikey) = openbabel.to_inchi(data, input_format)

    mol = {
        'inchi': inchi,
        'inchikey': inchikey,
        'name': name
    }

    mol = Molecule().create_xyz(user, mol, public=False)

    # These are normally performed in the molecule resource _clean() function
    del mol['access']
    mol['_id'] = str(mol['_id'])

    yield mol

    # Delete mol
    Molecule().remove(mol)

# Our method for creating a calculation
@pytest.fixture
def calculation(user, molecule):
    from girder.plugins.molecules.models.calculation import Calculation

    assert '_id' in molecule

    dir_path = os.path.dirname(os.path.realpath(__file__))

    # This cjson should match the molecule
    with open(dir_path + '/data/ethane.cjson', 'r') as rf:
        ethane_cjson = rf.read()

    # Let's make some properties
    properties = {
        "molecular mass": 30.0690,
        "melting point": -172,
        "boiling point": -88
    }

    _calc = Calculation().create_cjson(user, ethane_cjson, properties,
                                       molecule['_id'], notebooks=[],
                                       public=False)

    calc = Calculation().filter(_calc, user)

    yield calc

    # Delete calc
    Calculation().remove(calc)
