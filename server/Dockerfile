# N-Ways Addressing for Guinea-Bissau: registry server.
# Build from the repository root:  docker build -f server/Dockerfile -t addresses-gw .
# or simply:                        cd server && docker compose up -d
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ADDRESSES_DB=/data/addresses.sqlite \
    PORT=8080

WORKDIR /app
RUN useradd --system --uid 10001 --no-create-home --home-dir /app addresses \
 && mkdir -p /data && chown addresses:addresses /data

COPY engine/ engine/
COPY model/ model/
COPY registry/ registry/
COPY server/ server/
COPY LICENSE LICENSE-DATA LICENSE-DOCS LICENSING.md NOTICE ./

USER addresses
VOLUME ["/data"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
  CMD python3 -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/v1/health' % os.environ.get('PORT', '8080'), timeout=4)"

ENTRYPOINT ["sh", "/app/server/entrypoint.sh"]
