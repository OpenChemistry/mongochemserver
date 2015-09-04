# -*- coding: utf-8 -*-

from .molecule import Molecule
from .calculation import Calculation


def load(info):
    info['apiRoot'].molecules = Molecule()
    info['apiRoot'].calculations = Calculation()
