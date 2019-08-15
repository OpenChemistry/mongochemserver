import json

from flask import Flask
from flask import request

import openbabel_api as openbabel

app = Flask(__name__)


@app.route('/convert/<output_format>', methods=['POST'])
def convert(output_format):
    """Convert molecule data from one format to another via OpenBabel

    The output format is specified in the path. The input format and
    the data are specified in the body (in json format) as the keys
    "format" and "data", respectively.

    Some options may also be specified in the json body. The following
    options will be used in all cases other than the special ones:

        gen3d (bool): should we generate 3d coordinates?
        addHydrogens (bool): should we add hydrogens?
        outOptions (dict): what extra output options are there?

    Special cases are:
        output_format:
            svg: returns the SVG
            smi: returns canonical smiles
            inchi: returns json containing "inchi" and "inchikey"

    Curl example:
    curl -X POST 'http://localhost:5000/convert/inchi' \
      -H "Content-Type: application/json" \
      -d '{"format": "smiles", "data": "CCO"}'
    """
    json_data = request.get_json()
    input_format = json_data['format']
    data = json_data['data']

    # Treat special cases with special functions
    out_lower = output_format.lower()
    if out_lower == 'svg':
        return openbabel.to_svg(data, input_format)
    elif out_lower in ['smiles', 'smi']:
        return openbabel.to_smiles(data, input_format)
    elif out_lower == 'inchi':
        inchi, inchikey = openbabel.to_inchi(data, input_format)
        d = {
            'inchi': inchi,
            'inchikey': inchikey
        }
        return json.dumps(d)

    # Check for a few specific arguments
    gen3d = json_data.get('gen3d', False)
    add_hydrogens = json_data.get('addHydrogens', False)
    out_options = json_data.get('outOptions', {})

    return openbabel.convert_str(data, input_format, output_format,
                                 gen3d=gen3d, add_hydrogens=add_hydrogens,
                                 out_options=out_options)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
