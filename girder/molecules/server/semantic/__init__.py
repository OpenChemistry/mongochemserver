from . import gainesville
from . import cheminf
from . import virtuoso

def upload_molecule(mol):
    gainesville_graph = gainesville.create_molecule_graph(mol)
    gainesville_id = '%s_gainesville' % mol['_id']
    virtuoso.upload_rdf(gainesville_id, gainesville_graph)

    cheminf_graph = cheminf.create_molecule_graph(mol)
    cheminf_id = '%s_cheminf' % mol['_id']
    virtuoso.upload_rdf(cheminf_id, cheminf_graph)
