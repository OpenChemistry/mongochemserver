Running the Open Babel Flask Server Locally
===========================================

To run the Open Babel flask server locally, install the
requirements.txt file and start the server like so:
```
pip install -r requirements.txt
python src/server.py
```

It will, by default, be available at `http://localhost:5000`.

You can then test it with curl commands such as:
```
curl -X POST 'http://localhost:5000/convert/inchi' \
  -H "Content-Type: application/json" \
  -d '{"format": "smiles", "data": "CCO"}'
```

The server may also be started using a production WSGI server. For
instance, gunicorn can be used like so:
```
cd src
gunicorn -w 4 -t 600 server:app -b 0.0.0.0:5000
```
