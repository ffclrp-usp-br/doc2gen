FROM python:3.12-slim-trixie

# Dependências de sistema para build de mysqlclient e cliente mysql (mysqladmin)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    default-libmysqlclient-dev \
    libmariadb-dev \
    mariadb-client \
    pkg-config \
    curl \
    lynx \
    iputils-ping \
    nmap \
 && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv
RUN useradd -ms /bin/bash python

USER python

WORKDIR /home/python/app

ENV PIPENV_IN_PROJECT=True

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# As migration depends on db service availability, run migrate in compose command

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

