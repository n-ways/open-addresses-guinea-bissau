#!/bin/sh
# Container start: import the bundled registry on first start (empty volume), then serve.
set -e
DB="${ADDRESSES_DB:-/data/addresses.sqlite}"
if [ ! -s "$DB" ]; then
  echo "first start: importing the registry into $DB" >&2
  python3 -m server import --registry /app/registry --db "$DB"
fi
exec python3 -m server serve --db "$DB" --port "${PORT:-8080}"
