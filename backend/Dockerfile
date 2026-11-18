FROM python:3.14-slim

ENV PYTHONPATH=/app/backend \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

# Editable install on purpose: the catalog loader resolves its data
# directory relative to the source tree (four parents up from
# backend/app/modules/catalog/loader.py), which only lands on
# /app/catalog/services outside site-packages.
COPY backend/ /app/backend/
COPY catalog/ /app/catalog/
RUN pip install -e .

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin rinavi \
    && mkdir -p /data/vault \
    && chown -R rinavi:rinavi /data/vault

COPY backend/docker-entrypoint.sh /app/backend/docker-entrypoint.sh
RUN chmod +x /app/backend/docker-entrypoint.sh

USER rinavi

EXPOSE 8000

ENTRYPOINT ["/app/backend/docker-entrypoint.sh"]
