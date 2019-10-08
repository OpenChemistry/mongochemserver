Running the Avogadro Flask Server Locally
===========================================

To run the Avogadro flask server locally, install the
requirements.txt file and start the server like so:
```
pip install -r requirements.txt
python src/server.py
```

It will, by default, be available at `http://localhost:5001`.

You can then test it with curl commands:


To convert a string:
```
curl -X POST 'http://localhost:5001/convert-str/sdf' \
  -H "Content-Type: application/json" \
  -d "@path/to/file.json"
```

To get all molecule properties or just the atom count:
```
curl -X POST 'http://localhost:5001/properties/<type>' \
  -H "Content-Type: application/json" \
  -d "@path/to/file.json"
```
Where type = 'molecule' or 'atom', and file.json contains the format:
    '{
        "data": {
            /*molecule cjson*/
        },
        "format": "cjson"
    }'


To calculate MO:
```
curl -X POST 'http://localhost:5001/calculate-mo' \
  -H "Content-Type: application/json" \
  -d "@path/to/file.json"
```
Where file.json contains the format:
    '{
        "cjson": {
            /*calculation cjson*/
        },
        "mo": "homo"
    }'

The server may also be started using a production WSGI server. For
instance, gunicorn can be used like so:
```
cd src
gunicorn -w 4 -t 600 server:app -b 0.0.0.0:5001
```
