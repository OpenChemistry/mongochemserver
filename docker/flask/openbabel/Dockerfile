FROM python:3.7-slim

RUN apt-get update -y
RUN apt-get install -y \
  build-essential \
  pkg-config \
  libopenbabel-dev \
  swig

COPY flask/openbabel/requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

COPY flask/openbabel/src/* /app/

WORKDIR /app

ENTRYPOINT ["python3", "server.py"]
