from girder.utility.model_importer import ModelImporter
import requests

from molecules.constants import PluginSettings

def upload_rdf(_, rdf):
    settings = ModelImporter.model('setting')

    base_url = settings.get(PluginSettings.JENA_BASE_URL, 'http://jena-fuseki:3030')
    user = settings.get(PluginSettings.JENA_USER)
    password = settings.get(PluginSettings.JENA_PASSWORD)
    dataset = settings.get(PluginSettings.JENA_DATASET)

    base_url = base_url.rstrip('/')

    url = '%s/%s/data' % (base_url, dataset)
    headers = {
        'Content-Type': 'application/rdf+xml'
    }

    r = requests.post(url, headers=headers, data=rdf, auth=(user, password))
    r.raise_for_status()
