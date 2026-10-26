FROM python:3.13

RUN mkdir -p /opt/service

WORKDIR /opt/service

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ddl ddl
COPY bin bin
COPY lib lib

ENV PYTHONPATH="/opt/service/lib"

CMD ["/opt/service/bin/api.py"]
