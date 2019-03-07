FROM girder/girder:2.x-maintenance-py3

# Install cumulus
RUN git clone https://github.com/Kitware/cumulus.git /cumulus && \
  pip install --no-cache-dir -r /cumulus/requirements.txt && \
  pip install --no-cache-dir -e /cumulus && \
  girder-install plugin /cumulus/girder/cumulus && \
  girder-install plugin /cumulus/girder/sftp && \
  girder-install plugin /cumulus/girder/newt && \
  girder-install plugin /cumulus/girder/taskflow

# Set the broker URL
RUN sed -i s/localhost/rabbitmq/g /cumulus/cumulus/celery/commonconfig.py

COPY docker/config.json /cumulus/cumulus/conf/config.json

RUN git clone https://github.com/OpenChemistry/openchemistrypy.git /openchemistrypy

# Install deps for pybel
RUN apt-get update && apt-get -y install \
  swig \
  libopenbabel-dev

# Enable proxy support
COPY docker/girder.local.conf /girder/girder/conf/girder.local.cfg

# Copy over mongochemserver
COPY . /mongochemserver

# Install mongochemserver
RUN pip  install --no-cache-dir -r /mongochemserver/requirements.txt && \
  girder-install plugin /mongochemserver/girder/molecules && \
  girder-install plugin /mongochemserver/girder/notebooks && \
  girder-install plugin /mongochemserver/girder/queues && \
  girder-install plugin /mongochemserver/girder/app

# Install clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
