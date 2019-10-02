import json

from flask import Flask, Response, request

import avogadro_api as avogadro

app = Flask(__name__)


@app.route('/calculate-mo', methods=['POST'])
def calculate():
    json_data = request.get_json()

    # Make sure cjson and mo exist and are not empty
    if 'cjson' not in json_data or 'mo' not in json_data:
        return Response(json_data, status=400, mimetype='application/json')
    else:
        cjson = json_data['cjson']
        mo = json_data['mo']
        if not cjson or not mo:
            return Response(cjson, status=400, mimetype='application/json')

    # Prevent potential segfault by checking for electronic structure
    if ('basisSet' not in json_data['cjson']
            or 'orbitals' not in json_data['cjson']):
        return Response(
            json_data['cjson'], status=400, mimetype='application/json')

    return avogadro.calculate_mo(cjson, mo)


@app.route('/convert-str/<output>', methods=['POST'])
def convert_string(output):
    json_data = request.get_json()

    # Make sure format and data exist and are not empty
    if 'format' not in json_data or 'data' not in json_data:
        return Response(json_data, status=400, mimetype='application/json')
    else:
        input_format = json_data['format']
        data = json.dumps(json_data['data'])
        if not input_format or not data:
            return Response(json_data, status=400, mimetype='application/json')

    return avogadro.convert_str(data, input_format, output)


@app.route('/properties/<property_type>', methods=['POST'])
def get_properties(property_type):
    json_data = request.get_json()

    # Make sure format and data exist and are not empty
    if 'format' not in json_data or 'data' not in json_data:
        return Response(json_data, status=400, mimetype='application/json')
    else:
        input_format = json_data['format']
        data = json.dumps(json_data['data'])
        if not input_format or not data:
            return Response(json_data, status=400, mimetype='application/json')

    if property_type == 'molecule':
        return avogadro.molecule_properties(data, input_format)
    elif property_type == 'atom':
        return str(avogadro.atom_count(data, input_format))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
