# Registry server

A ready-to-deploy HTTP service for the N-Ways addresses of Guinea-Bissau. It serves exactly the codes published in [`registry/`](../registry/) (241,673 compounds in 39 sectors) through a JSON API, and, on the one deployment designated to issue, gives new compounds their codes by the same rules as the N-Ways issuer, so every deployment gives the same answer for the same code.

- Python 3.9 or later, standard library only. The code forms, check digits, spot codes and numbering come from the reference engine in [`engine/reference/`](../engine/reference/).
- SQLite storage (WAL mode), with an R\*Tree spatial index, or an integer grid where SQLite lacks R\*Tree.
- Every endpoint, with real requests and responses: [`docs/api.md`](../docs/api.md). Machine-readable description: [`openapi.yaml`](openapi.yaml) (OpenAPI 3.1).

## Deploy with Docker

From this folder:

```sh
docker compose up -d
curl -s http://localhost:8080/v1/health
```

On its first start the container imports the bundled registry into its volume (under a minute, about 120 MB on disk), checking every file against `MANIFEST.json`; then it serves on port 8080. Later starts reuse the database. The image runs as an unprivileged user and has a health check on `/v1/health`.

To build and run the image without Compose, from the repository root:

```sh
docker build -f server/Dockerfile -t addresses-gw .
docker run -d --name addresses -p 8080:8080 -v addresses-data:/data addresses-gw
```

## Run with plain Python

From the repository root:

```sh
python3 -m server import --registry registry --db data/addresses.sqlite
python3 -m server serve --db data/addresses.sqlite --port 8080
```

`import` streams every `registry/*.csv.gz` into a new database, verifies the SHA-256 of each file and every count against `MANIFEST.json`, and replaces the database only when everything matches. It can be run again at any time; it refuses to replace a database that holds codes issued since its import (export them first, or pass `--force`).

`python3 -m server export --db data/addresses.sqlite --out exported/` writes the registry back in the published format: one `<SECTOR>.csv.gz` per sector, `areas.csv.gz` (and `areas.csv`), and `MANIFEST.json`, compressed without a file name or time stamp (`gzip -n`). After an import of the published registry the export is byte-identical to it once uncompressed (the SHA-256 digests in `MANIFEST.json` are of the uncompressed files; the compressed bytes depend on the zlib build); after issuing, it carries the new codes and any continuation blocks.

## Configure

| Variable | Flag | Default | Meaning |
|---|---|---|---|
| `ADDRESSES_DB` | `--db` | `data/addresses.sqlite` (`/data/addresses.sqlite` in Docker) | the database file |
| `PORT` | `--port` | `8080` | the port to listen on |
| `HOST` | `--host` | `0.0.0.0` | the address to listen on |
| `ISSUE_KEYS` | | empty | comma-separated bearer keys allowed to issue and change codes; empty means read-only |
| `ISSUE_PER_DAY` | | `5` | new codes each key may issue in any 24 hours |
| `CORS_ORIGINS` | | empty | comma-separated origins allowed to call the API from a browser, or `*` |

With Compose, put the variables in a `.env` file next to `docker-compose.yml` (never commit it) or in the environment of the shell that runs `docker compose up`. Generate a key with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`.

## Behind a reverse proxy with TLS

Serve the API over HTTPS only. A minimal Caddy configuration, which obtains and renews the certificate itself:

```
addresses.example.gw {
    reverse_proxy 127.0.0.1:8080
}
```

The same with nginx (certificate from Let's Encrypt or the State's certificate authority):

```nginx
server {
    listen 443 ssl;
    server_name addresses.example.gw;
    ssl_certificate     /etc/ssl/addresses/fullchain.pem;
    ssl_certificate_key /etc/ssl/addresses/privkey.pem;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 64k;
    }
}
```

Bind the server to the proxy only (`--host 127.0.0.1`, or `ports: ["127.0.0.1:8080:8080"]` in Compose) so that it is not reachable around the proxy. Rate limiting of read requests, if needed, belongs in the proxy.

## Back up

The database is one SQLite file. Take a consistent copy while the server runs with:

```sh
sqlite3 data/addresses.sqlite ".backup 'backup/addresses-$(date +%F).sqlite'"
```

In Docker, run the same inside the container (`docker compose exec addresses python3 -c "import sqlite3; s=sqlite3.connect('/data/addresses.sqlite'); s.backup(sqlite3.connect('/data/backup.sqlite'))"`) and copy the file out with `docker compose cp`. An issuing deployment should also export the registry every day (`python3 -m server export`) and keep the exports: they are the public record of every code, in the published format.

## Update to a newer registry

A read-only deployment follows the published registry:

```sh
git pull                                    # the new registry/ and MANIFEST.json
python3 -m server import --registry registry --db data/addresses.sqlite
# restart the server
```

With Docker: `git pull`, `docker compose build`, then remove the volume's database (`docker compose down -v`) and `docker compose up -d` to import the new registry on start.

An issuing deployment does not re-import: its database is the source of the codes it issued. It publishes them with `export`.

## One issuer

Only one deployment in the country may issue codes. A deployment issues only when the State, or N-WAYS LIMITED on the State's behalf, has designated it as the issuer; every other deployment runs read-only, without `ISSUE_KEYS`.

The reason is arithmetic. A number is unique because the issuer that gives it knows every number already given in its area and every block already taken by its name. Two issuers working from the same registry would each see the same free number and give it to two different compounds, and two homes would share one address. The registry would no longer be a register. Read-only copies have no such risk: they can be run by any ministry, municipality, post office, emergency service or company, as many as are needed, and all give the same answers.

When the designated issuer changes, the new issuer imports the outgoing issuer's last export and the outgoing deployment becomes read-only, in that order.

## The issuing rules

`POST /v1/codes` follows the issuer step by step (engine/SPEC.md 5.1 and 7.2):

1. The point must fall inside one of the 39 sectors and lie inside the national border or within 300 m of it (engine/SPEC.md 3.1). The border is OpenStreetMap's admin_level 2 boundary of Guinea-Bissau, shipped simplified in `engine/data/border.geojson` with the limit reduced by the simplification's largest deviation (248 m of the simplified line), so a point accepted is never more than 300 m outside the true border. A sector outline that spills over the border never carries a code into a neighbouring country: such a point is refused with `422 outside`, and `GET /v1/at` answers `outside` there.
2. A new compound is refused when a live code's entrance, or an outline recorded by this deployment, lies within 3 m of the point, or when the outline sent overlaps a recorded one by more than half of the smaller. An outline must enclose between 6 m² and 2 ha.
3. Another door (`of`) must be within 80 m of that code's entrance, and takes that code's area.
4. A new compound takes the nearest place of its sector on the same land mass (Ilha de Bissau counts with the mainland) within 3 km, else the sector's own word.
5. Its number lies between its two neighbours along the Hilbert curve in one of the area's blocks, else after the area's highest number; when every block is full, the area takes a continuation block sized for its compounds, above the name's high-water mark. Earlier numbers never change and a number is never reused, retired ones included.
6. The code is `provisional` and marked `on-demand`. `PATCH` confirms or retires it, or moves its entrance by up to 80 m, never across the border (`422 outside`).

The test suite replays a sequence of requests in the Komo sector, including a block that fills and an area with no block yet, and checks every number and form against the N-Ways issuer's own output for the same requests (`server/testdata/parity-expected.json`).

## Entrance points and building outlines

A registry row locates a compound by its entrance point; building outlines are public datasets of their own (OpenStreetMap, Google Open Buildings, Microsoft) and are not repeated in it. The issuer also uses building outlines to decide which compound a point belongs to, so for a point inside a large building more than 12 m from its entrance, `/v1/at` here answers `none` where the issuer may name the building. Outlines sent with `POST /v1/codes` are recorded and used in the same way as the issuer uses its own.

## Tests

```sh
python3 -m unittest server.tests.test_server
python3 server/testdata/build.py      # rebuild the fixture from registry/
```

The tests use `server/testdata/registry` (the real codes of the Komo sector and the whole area table) in a temporary database: import and export round trip, every endpoint and its errors, issuing parity, continuation blocks, the duplicate checks, the national border, the daily limit and the HTTP layer.
