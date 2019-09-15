FROM python:3.7-slim

RUN apt-get update -y
RUN apt-get install -y \
  build-essential \
  pkg-config

RUN pip3 install gunicorn

COPY flask/avogadro/requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

COPY flask/avogadro/src/* /app/

WORKDIR /app

ENTRYPOINT ["gunicorn", "-w",  "4", "-t", "600", "server:app", "-b", "0.0.0.0:5000"]
