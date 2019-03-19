from . import gainesville
from . import cheminf
from . import jena

from girder.utility.model_importer import ModelImporter
from molecules.constants import PluginSettings

def upload_molecule(mol):
    settings = ModelImporter.model('setting')
    uri_base = settings.get(PluginSettings.SEMANTIC_URI_BASE, 'http://localhost:8888')
    uri_base = uri_base.rstrip('/')

    gainesville_graph = gainesville.create_molecule_graph(uri_base, mol)
    gainesville_id = '%s_gainesville' % mol['_id']
    jena.upload_rdf(gainesville_id, gainesville_graph)

    cheminf_graph = cheminf.create_molecule_graph(uri_base, mol)
    cheminf_id = '%s_cheminf' % mol['_id']
    jena.upload_rdf(cheminf_id, cheminf_graph)
