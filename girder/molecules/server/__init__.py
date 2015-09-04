# -*- coding: utf-8 -*-

from .molecule import Molecule


def load(info):
    info['apiRoot'].molecules = Molecule()
