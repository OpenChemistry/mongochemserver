Running the Avogadro Flask Server Locally
===========================================

To run the Avogadro flask server locally, install the
requirements.txt file and start the server like so:
```
pip install -r requirements.txt
python src/server.py
```

It will, by default, be available at `http://localhost:5000`.

You can then test it with curl commands such as:
```
curl -X POST 'http://localhost:5000/calculate' \
  -H "Content-Type: application/json" \
  -d "@path/to/file.json"
```
Where file.json contains the format:
    '{
        "cjson": {
            /*cjson data*/
        },
        "mo": mo
    }'

The server may also be started using a production WSGI server. For
instance, gunicorn can be used like so:
```
cd src
gunicorn -w 4 -t 600 server:app -b 0.0.0.0:5000
```