Running the Docker Container
============================

Running the docker container locally can be done as simply as this:
```
# Update the docker image if needed
docker pull openchemistry/avogadro

# Run it
docker run -p 5001:5001 openchemistry/avogadro
```

Mongochemserver falls back on port 5001 for Avogadro if one was
not specified, so port 5001 will hopefully work.

Building the Docker Container
=============================

From the top-level directory of mongochemserver, run this command:
```
docker build . \
  -t openchemistry/avogadro \
  -f ./docker/flask/avogadro/Dockerfile
```
