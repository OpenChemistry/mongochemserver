import os
import sys
import json
import argparse
from girder_client import GirderClient, HttpError

def import_calc(config):
    try:
        client = GirderClient(host=config.host, port=config.port)
        client.authenticate(config.username, config.password)

        if not config.moleculeId:
            with open(config.sdf, 'r') as fp:
                sdf = fp.read()
            parts = os.path.basename(config.sdf).split('.')
            body = {
                'name': parts[0],
                'sdf': sdf
            }

            mol = client.sendRestRequest('POST', 'molecules', data=json.dumps(body))
            config.moleculeId = mol['_id']

        with open(config.modes, 'r') as fp:
            modes = json.load(fp)

        body = {
            'vibrationalModes': modes,
            'sdf': sdf,
            'moleculeId': config.moleculeId
        }
        client.sendRestRequest('POST', 'calculations', data=json.dumps(body))


    except HttpError as error:
        print(error.responseText, file=sys.stderr)

if __name__ ==  '__main__':
    parser = argparse.ArgumentParser(description='Command to import calculation')

    parser.add_argument('--host', help='Girder host', required=True)
    parser.add_argument('--port', help='Girder port', required=True)
    parser.add_argument('--username', help='Girder username', required=True)
    parser.add_argument('--password', help='Girder password', required=True)
    parser.add_argument('--sdf', help='Path to SDF file', required=True)
    parser.add_argument('--modes', help='JSON file contain modes', required=True)
    parser.add_argument('--moleculeId', help='The molecule to associate this calculation with', required=False)

    config = parser.parse_args()
    import_calc(config)