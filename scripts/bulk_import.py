import os
import sys
import json
import argparse
from girder_client import GirderClient, HttpError

def import_calc(config):
    try:
        target_port = None
        if config.port:
            target_port = config.port
        target_scheme = None
        if config.scheme:
            target_scheme = config.scheme
        target_apiroot = None
        if config.apiroot:
            target_apiroot = config.apiroot

        client = GirderClient(host=config.host, port=target_port,
                              scheme=target_scheme, apiRoot=target_apiroot)
        client.token = config.token

        me = client.get('/user/me')

        folderParams = {
            'parentId': me['_id'],
            'parentType': 'user',
            'name': 'Private'
        }

        # Get the private folder id first
        folder = client.listResource('folder', folderParams)

        folder = client.listFolder(me['_id'], 'user', 'Private')

        for file_name in config.datafile:
            print ('\nUploading ' + file_name)
            file_id = {}
            with open(file_name, 'r') as fp:
                fileNameBase = os.path.basename(file_name)
                size = os.path.getsize(file_name)
                file_id = client.uploadFile(folder[0]['_id'], fp, fileNameBase,
                                            size, 'folder')

            body = { 'fileId': file_id['_id'] }

            mol = client.sendRestRequest('POST', 'molecules', data=json.dumps(body))

            config.moleculeId = mol['_id']
            print('Molecule ID: ' + mol['_id'])

    except HttpError as error:
        print(error.responseText, file=sys.stderr)

if __name__ ==  '__main__':
    parser = argparse.ArgumentParser(description='Command to import calculation')

    parser.add_argument('--host', help='Girder host', required=True)
    parser.add_argument('--port', help='Girder port', required=False)
    parser.add_argument('--scheme', help='Transport, http or https', required=False)
    parser.add_argument('--apiroot', help='API root for target', required=False)
    parser.add_argument('--token', help='Girder auth token', required=True)
    parser.add_argument('--datafile', help='Path to data file', nargs='*', required=False)
    parser.add_argument('--modes', help='JSON file contain modes', required=False)
    parser.add_argument('--moleculeId', help='The molecule to associate this calculation with', required=False)

    config = parser.parse_args()
    import_calc(config)
