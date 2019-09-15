from flask import Flask, jsonify, request, Response

import avogadro_api as avogadro

app = Flask(__name__)

@app.route('/calculate', methods=['POST'])
def calculate():
    json_data = request.get_json()
    cjson = json_data['cjson']
    mo = json_data['mo']
    calc = avogadro.calculate_mo(cjson, mo)

    return calc


if __name__ == '__main__':
    app.run(host='0.0.0.0')