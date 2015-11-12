from . import gainesville
from . import cheminf
from . import virtuoso

from girder.utility.model_importer import ModelImporter
from girder.plugins.molecules.constants import PluginSettings

def upload_molecule(mol):
    settings = ModelImporter.model('setting')
    uri_base = settings.get(PluginSettings.SEMANTIC_URI_BASE, 'http://openchemistry.kitware.com')
    uri_base = uri_base.rstrip('/')

    gainesville_graph = gainesville.create_molecule_graph(uri_base, mol)
    gainesville_id = '%s_gainesville' % mol['_id']
    virtuoso.upload_rdf(gainesville_id, gainesville_graph)

    cheminf_graph = cheminf.create_molecule_graph(uri_base, mol)
    cheminf_id = '%s_cheminf' % mol['_id']
    virtuoso.upload_rdf(cheminf_id, cheminf_graph)
