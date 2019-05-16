from rdflib import Namespace, Graph, URIRef
from rdflib.term import BNode, Literal
from rdflib.namespace import RDF, OWL, NamespaceManager


cheminf = Namespace('http://semanticscience.org/resource/')


def create_molecule_graph(uri_base, mol):
    mongochem = Namespace('%s/api/v1/molecules/' % uri_base)
    g = Graph()
    inchi = mol['inchi']
    name = mol.get('name')
    inchi_node = BNode()

    molecule = URIRef(mongochem[mol['_id']])

    namespace_manager = NamespaceManager(g)
    namespace_manager.bind('cheminf', cheminf, override=False)
    namespace_manager.bind('mongochem', mongochem, override=False)
    namespace_manager.bind('owl', OWL, override=False)

    g.add((molecule, OWL.subClassOf, cheminf.CHEMINF_000000))

    if name is not None:
        g.add((molecule, OWL.label, Literal(name.lower())))

    g.add((inchi_node, RDF.type, cheminf.CHEMINF_000113))
    g.add((inchi_node, cheminf.SIO_000300, Literal(inchi)))
    g.add((molecule, cheminf.CHEMINF_000200, inchi_node))

    return g.serialize()
