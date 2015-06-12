from girder.utility.model_importer import ModelImporter
import requests

from girder.plugins.molecules.constants import PluginSettings

def upload_rdf(id, rdf):
    settings = ModelImporter.model('setting')

    user = settings.get(PluginSettings.VIRTUOSO_USER)
    password = settings.get(PluginSettings.VIRTUOSO_PASSWORD)
    base_url = settings.get(PluginSettings.VIRTUOSO_BASE_URL, 'http://localhost:8890')
    upload_path  = settings.get(PluginSettings.VIRTUOSO_RDF_UPLOAD_PATH, 'DAV/home/mongochem/rdf_sink')

    base_url = base_url.rstrip('/')
    upload_path = upload_path.strip('/')

    url = '%s/%s/%s.rdf' % (base_url, upload_path, id)
    headers = {
        'content-type': 'application/rdf+xml'

    }

    r = requests.put(url, headers=headers, data=rdf, auth=(user, password))
    r.raise_for_status()
