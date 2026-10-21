# N-Ways Addressing for Guinea-Bissau

**Status: issued.** Every compound in Guinea-Bissau, in all 39 sectors, has an N-Ways code: 241,673 of them, issued on 20 October 2026 and provisional until residents confirm them. The complete registry is published here, every code with its entrance point and building profile. Guinea-Bissau has no official door-level address system (its postcodes exist on paper only: UPU, 2005, `1000 BISSAU`), so these are N-Ways addresses, designed to be adopted by the State.

A home's code is **a place word people already use plus a short number**:

| Remembered and written | Machine form (systems) | What it is |
|---|---|---|
| `Bandim 537` | `10-022-00537-4` | the compound nearest Bandim market, Bissau |
| `Bandim 275.2` | `10-022-00275.2-3` | the second structure of Bandim 275 |
| `Bandim 2001` | `93-005-02001-3` | a compound in Bandim, the tabanca of the same name in Catió |
| `Atufa 15` | `75-039-00015-0` | a family compound in Atufa, a morança cluster near Apurnia (Nhacra) |
| (a link) | `10-4327-9117` | a spot code: any point, computed offline |

The remembered form is unique in the whole country on its own. Every place with the same name shares one national number range (1-99,999), split into frozen blocks, one per place, so no town, sector or phone position is needed to tell two Bandims apart. Plates and written addresses show the place word and the number only; the machine form adds a check digit that binds the name, the number and, through the frozen block table, the place, so a system refuses a mistyped code instead of sending someone to the wrong door.

The place word is a short **plate name**: at most 12 characters and 2 words ("Ama Sidi 1001" for the tabanca whose official name is Missirá Ama Sidi). The official name still finds the place when typed. 356 places in use carry a provisional plate name until the Câmara Municipal or their sector chooses one; their compounds have their codes, and the number never changes.

## What is where

| Path | Contents |
|---|---|
| [docs/paper.md](docs/paper.md), [paper.pt.md](docs/paper.pt.md), [paper.fr.md](docs/paper.fr.md) | the research paper in English, Portuguese and French: the model with every formula and worked examples, its evaluation on the full registry, the designs considered, and the benefits for citizens, logistics, emergency services and government; typeset PDFs beside them |
| [docs/paper/](docs/paper/), [docs/figures/](docs/figures/) | the LaTeX typesetting of the paper (template, style, references) and its figures as TikZ sources with their data tables, compiled to PDF and SVG |
| [docs/api.md](docs/api.md) | every endpoint of the registry API, with real requests and responses |
| [docs/existing-systems.md](docs/existing-systems.md) | the postal and address systems that exist today (postcodes on paper only) |
| [docs/model.md](docs/model.md) | the design notes behind every choice |
| [engine/SPEC.md](engine/SPEC.md) | the engine specification (normative) |
| [engine/reference/](engine/reference/) | the reference engine `gw_codes.py` and `plate_names.py` (Python standard library only), its unit tests `test_gw.py` and the conformance vectors `vectors.json` every implementation must reproduce |
| [engine/data/](engine/data/) | what a decoder ships: `register.json` (sectors, every place with its plate name, aliases, name key and frozen blocks), the sector and island outlines, and the national border `border.geojson` |
| [registry/](registry/) | every issued code: one gzip CSV per sector (`BIS.csv.gz` ...), the frozen area table `areas.csv`, and `MANIFEST.json` (counts and the SHA-256 of every file) |
| [server/](server/) | a ready-to-deploy registry server and JSON API (Docker or plain Python), with its OpenAPI description and tests |
| [model/](model/) | `name-ranges.json` (the national range and blocks of every name), `places.json`, `sectors.json`, `regions.json`, `building-stats.json`, `design.json`, `coverage.geojson` |
| [tools/](tools/) | the scripts that built the sectors, the places, the plate names, the border, the compounds and the registry ([tools/README.md](tools/README.md)) |
| [GOVERNANCE.md](GOVERNANCE.md), [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) | rules for change, the single-issuer rule, how to propose a change and how to report a problem |
| [LICENSING.md](LICENSING.md), [NOTICE](NOTICE), [SOURCES.md](SOURCES.md), [CITATION.cff](CITATION.cff) | licences and how to credit, every source, how to cite the paper |

## Run the reference engine

```sh
python3 engine/reference/gw_codes.py                    # test vectors
python3 engine/reference/test_gw.py                     # unit tests
python3 engine/reference/gw_codes.py 11.8521 -15.5951   # spot code and place word for a point
python3 engine/reference/gw_codes.py 10-022-00537-4     # check and decode a machine code
python3 engine/reference/gw_codes.py "Bandim 537"       # resolve a remembered form, nationally
```

Python 3.9 or newer, no packages (see [requirements.txt](requirements.txt)).

## Run the server

The server serves the registry through a JSON API and gives identical answers wherever it runs:

```sh
cd server && docker compose up -d                       # import on first start, then serve on :8080
curl -s 'http://localhost:8080/v1/find?q=Bandim%20537'
```

or, without Docker, from the repository root:

```sh
python3 -m server import --registry registry --db data/addresses.sqlite
python3 -m server serve --db data/addresses.sqlite --port 8080
python3 -m unittest server.tests.test_server            # its tests
```

A deployment is read-only unless it is the designated issuer (one per country; see [server/README.md](server/README.md)). Endpoints, with real responses: [docs/api.md](docs/api.md).

## Build the paper

```sh
python3 tools/paper_figures.py   # the figures' data tables, from the published registry
sh docs/paper/build.sh           # figures, then the English, Portuguese and French PDFs in docs/
```

The build needs pandoc 3, tectonic and pdftocairo (poppler).

## How the registry was made

```sh
python3 tools/build_border.py build westafrica-admin.osm.pbf      # engine/data/border.geojson (the national border)
python3 tools/extract-buildings.py <work>                       # every footprint (DuckDB, 3 GB cap)
python3 tools/building-stats.py <work>                          # compounds, places, blocks, statistics
python3 tools/issue_registry.py <work> <work>/lotes.jsonl.gz     # one line per compound, sector by sector
python3 tools/export_register.py                                # engine/data/register.json
python3 tools/vectors.py                                        # engine/reference/vectors.json
python3 tools/build_border.py check                             # after every export: no code beyond the border
```

**The border decides.** A code is only ever issued for a building whose entrance lies inside the national border, OpenStreetMap's admin_level 2 boundary of Guinea-Bissau, or within 300 m of it, whatever a sector outline says (engine/SPEC.md 3.1). Grouping drops every footprint and compound beyond it, and the server refuses to issue a code or move an entrance there.

The N-Ways issuer then numbers the compounds again with its own implementation, refuses the run if any number differs from the reference's, issues the codes and exports `registry/`. The block table is frozen since the first issue: a later run adds codes for new compounds and never renumbers an issued one.

## Licence and credit

Code (engine, server, tools): Apache License 2.0, with [NOTICE](NOTICE). Data (registry, model, engine data): ODbL 1.0. Documents: CC BY 4.0. Credit every use: **"N-Ways Addressing for Guinea-Bissau, © N-WAYS LIMITED (nways.ng)"**, with a link to this repository ([LICENSING.md](LICENSING.md)). Derived from OpenStreetMap (© OpenStreetMap contributors, ODbL), Google Open Buildings (CC BY 4.0), Microsoft building footprints (ODbL) and GeoNames (CC BY 4.0).
