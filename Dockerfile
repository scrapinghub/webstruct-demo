FROM python:3.6.6-slim

RUN apt-get update -qq && \
    apt-get install -qy \
        git \
        gcc \
        g++ \
        && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /install
COPY requirements.txt /install
RUN pip install -r /install/requirements.txt
RUN pip install git+https://github.com/Supervisor/supervisor.git@5112520
COPY supervisord.conf /install/
COPY gunicorn /install
RUN chmod u+x /install/gunicorn
COPY src /install/src
COPY build/model.joblib /install
RUN echo "MODEL_PATH='/install/model.joblib'" > /install/src/instance/config.py

ENTRYPOINT ["supervisord", "-c", "/install/supervisord.conf", "--nodaemon"]
