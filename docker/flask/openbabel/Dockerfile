FROM continuumio/miniconda3:4.7.12

RUN conda install -c conda-forge openbabel=3.0.0 -y

RUN pip install gunicorn

COPY flask/openbabel/requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY flask/openbabel/src/* /app/

WORKDIR /app

# By default, Open Babel does not release the python GIL while the underlying
# C++ code is running. This means that it is perhaps preferable for us to have
# multiple synchronous workers, rather than a single asynchronous worker.
# Hence, we are using multiple workers of the default "sync" worker class.
# Additionally, some operations on big molecules take a long time (commonly
# more than a minute). So we will set the timeout to be 10 minutes.
ENTRYPOINT ["gunicorn", "-w",  "4", "-t", "600", "server:app", "-b", "0.0.0.0:5000"]
