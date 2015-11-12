from rdflib import Namespace, Graph, URIRef
from rdflib.term import BNode, Literal
from rdflib.namespace import RDF, OWL, NamespaceManager
import requests
import argparse
import json
from jsonpath_rw import parse
from . import element

gc = Namespace('http://purl.org/gc/#')
pt = Namespace('http://www.daml.org/2003/01/periodictable/PeriodicTable#')

def create_molecule_graph(uri_base, mol):
    id = mol['_id']
    g = Graph()

    uri = '%s/api/v1/molecules/' % uri_base
    mongochem = Namespace(uri)

    molecule = URIRef(mongochem[id])

    namespace_manager = NamespaceManager(g)
    namespace_manager.bind('mongochem', mongochem, override=False)
    namespace_manager.bind('gc', gc, override=False)
    namespace_manager.bind('pt', pt, override=False)

    bond_count = len(parse('cjson.bonds.order').find(mol)[0].value)
    atomic_numbers = parse('cjson.atoms.elements.number').find(mol)[0].value
    coordinates_values = parse('cjson.atoms.coords').find(mol)[0].value['3d']
    atom_count = len(atomic_numbers)

    g.add((molecule, RDF.type, gc.Molecule))
    g.add((molecule, gc.hasNumberOfAtoms, Literal(str(atom_count))))
    g.add((molecule, gc.hasBondCount, Literal(str(bond_count))))
    g.add((molecule, gc.hasInchIKey, Literal(mol['inchikey'])))

    index = 0
    atoms = {}
    for a in atomic_numbers:
        uri = '%s/api/v1/molecules/%s/atoms/%d'  % (uri_base, id, index)
        atom = URIRef(uri)
        atoms[index] = atom
        g.add((atom, RDF.type, gc.Atom))
        g.add((atom, gc.isElement, pt.term(element.symbols[a])))
        mass = BNode()
        g.add((mass, RDF.type, gc.FloatValue))
        g.add((mass, gc.hasFloatValue, Literal(str(element.masses[a]))))
        g.add((mass, gc.hasUnit, gc.atomicUnit))
        g.add((atom, gc.hasMass, mass))

        coordinate_value = '%f %f %f' % (coordinates_values[index],
                                       coordinates_values[index + 1],
                                       coordinates_values[index + 2] )
        coordinates = BNode()
        g.add((coordinates, RDF.type, gc.VectorValue))
        g.add((coordinates, gc.hasVectorValue, Literal(coordinate_value)))
        g.add((coordinates, gc.hasUnit, gc.angstrom))
        g.add((atom, gc.hasCoordinates, coordinates))

        g.add((molecule, gc.hasAtom, atom))
        index += 1

    bonds = parse('cjson.bonds').find(mol)[0].value
    orders = bonds['order']
    connections = bonds['connections']['index']
    connections = list(zip(connections[::2], connections[1::2]))

    for b in range(0, len(orders)):
        order = orders[b]
        (from_atom, to_atom) = connections[b]

        bond_type = gc.term('Aromatic')
        if order == 1:
            bond_type = gc.term('Single')
        elif order == 2:
            bond_type = gc.term('Double')
        elif order == 3:
            bond_type = gc.term('Triple')
        elif order == 4:
            bond_type = gc.term('Quadruple')

        uri = '%s/api/v1/molecules/%s/bonds/a%d-a%d'  % (uri_base, id, from_atom, to_atom)
        bond = URIRef(uri)

        g.add((bond, RDF.type, bond_type))
        g.add((atoms[from_atom], gc.hasBond, bond))
        g.add((atoms[to_atom], gc.hasBond, bond))

    return g.serialize()


