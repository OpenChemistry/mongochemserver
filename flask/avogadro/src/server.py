import json

from flask import Flask, request

import avogadro_api as avogadro

app = Flask(__name__)


@app.route('/calculate-mo', methods=['POST'])
def calculate():
    json_data = request.get_json()
    cjson = json_data['cjson']
    mo = json_data['mo']

    return avogadro.calculate_mo(cjson, mo)


@app.route('/convert-str/<output>', methods=['POST'])
def convert_string(output):
    json_data = request.get_json()
    input_format = json_data['format']
    data = json_data['data']

    return avogadro.convert_str(data, input_format, output)


@app.route('/properties/<property_type>', methods=['POST'])
def get_properties(property_type):
    json_data = request.get_json()
    input_format = json_data['format']
    data = json_data['data']

    if property_type == 'molecule':
        return avogadro.molecule_properties(data, input_format)
    elif property_type == 'atom':
        return str(avogadro.atom_count(data, input_format))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
