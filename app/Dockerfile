# Build-Kontext ist das Projektwurzelverzeichnis (siehe docker-compose.yml).
FROM python:3.12.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# libmagic fuer echte MIME-Erkennung (nicht nur Dateiendung)
RUN apt-get update \
 && apt-get install -y --no-install-recommends libmagic1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY app/requirements.txt /srv/requirements.txt
RUN pip install -r /srv/requirements.txt

COPY app/klartext /srv/klartext
COPY migrations /srv/migrations
COPY THIRD_PARTY_LICENSES.md /srv/THIRD_PARTY_LICENSES.md

RUN useradd --uid 1000 --create-home --shell /usr/sbin/nologin klartext \
 && mkdir -p /data/uploads /data/results \
 && chown -R klartext:klartext /data /srv
USER klartext

EXPOSE 8000
