FROM python:3.6-slim-stretch

ENV PIP_TIMEOUT=180
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR="true"

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc git g++ && \
    rm -rf /var/lib/apt/lists/*


RUN pip install --upgrade pip
COPY requirements.txt /requirements.txt

RUN pip install -r requirements.txt

FROM python:3.6-slim-stretch

RUN mkdir -p /app /usr/local/var && \
    ln -s /app /usr/local/var/webstruct-demo-instance

WORKDIR /app

COPY --from=0 /usr/local/lib/python3.6/site-packages /usr/local/lib/python3.6/site-packages
COPY --from=0 /usr/local/bin/gunicorn /usr/local/bin/gunicorn

COPY ./src/webstruct-demo /app/webstruct-demo

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8080", "-w", "5", "webstruct-demo.__init__:webstruct_demo", "--log-file", "-", "--error-logfile", "-", "--access-logfile", "-"]
