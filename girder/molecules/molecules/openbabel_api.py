import requests

from girder.models.setting import Setting

from molecules.constants import PluginSettings


def openbabel_base_url():
    base_url = Setting().get(PluginSettings.OPENBABEL_BASE_URL)
    if base_url is None:
        base_url = 'http://localhost:5000'

    return base_url


def run_openbabel_convert(data, input_format, output_format, extra_options):

    base_url = openbabel_base_url()
    path = 'convert'
    url = '/'.join([base_url, path, output_format])

    json_data = {
        'format': input_format,
        'data': data,
    }
    json_data.update(extra_options)

    return requests.post(url, json=json_data)
