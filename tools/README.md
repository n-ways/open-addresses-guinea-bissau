# tools/

How the sectors, places, plate names, border and compounds of Guinea-Bissau were built (engine/SPEC.md), and the paper's figures. Python 3.9 or later; the heavy steps also need `duckdb` with its spatial extension. Run one heavy job at a time.

| Script | What it does |
|---|---|
| `make-sectors.py` | the 39 frozen sectors from the OpenStreetMap admin_level 6 relations and the Setor Autónomo de Bissau -> `model/sectors.json`, `engine/data/sectors.geojson` (SPEC 3) |
| `build_border.py build <extract.osm.pbf>` | the national border from the OpenStreetMap admin_level 2 relation of Guinea-Bissau -> `engine/data/border.geojson` (SPEC 3.1) |
| `build_border.py check` | counts the published codes whose entrance lies beyond the border; exits non-zero if there is any |
| `make-places.py` | the place table from OpenStreetMap and GeoNames -> `model/places.json` (SPEC 5.1) |
| `gw_plates.py` | the plate name of every place (SPEC 5.1.2) |
| `extract-buildings.py <work>` | every footprint with its raw profile facts, its sector, enclosure, island and places -> `<work>/buildings.csv` |
| `building-stats.py <work>` | the grouping into compounds, place words, blocks and numbers, and `model/building-stats.json` (SPEC 7, 8) |
| `issue_registry.py <work> <out.jsonl.gz>` | the same grouping, one JSON line per compound, for the issuer to number |
| `validate-grouping.py <work>` | the proximity rule checked against the compounds people drew |
| `export_register.py` | `engine/data/register.json` from the model files |
| `vectors.py` | the conformance vectors `engine/reference/vectors.json` |
| `paper_figures.py` | the data of every figure of the paper (`docs/figures/*.dat`), from the published registry |

## The border decides

A code is only ever issued for a building whose entrance lies inside the national border of Guinea-Bissau, OpenStreetMap's admin_level 2 boundary (`ISO3166-1=GW`), or within 300 m of it. Sector outlines, and outlines from any other source (geoBoundaries, GADM and the like), may spill over the border; none of them decides.

`build_border.py build` reads the relation tagged `boundary=administrative`, `admin_level=2`, `ISO3166-1=GW` from an OpenStreetMap extract with DuckDB's `ST_ReadOSM`, joins its member ways into closed rings, simplifies them by Douglas-Peucker at 50 m and writes `engine/data/border.geojson` (16 kB, coordinates to 1e-5 degrees). The extract must hold the relation whole: a country extract clipped at its own outline usually misses some border ways, and the tool then stops with "the border does not close". Use the region's boundary extract (`data/osm/westafrica-admin.osm.pbf` in an N-Ways checkout), or cut one with `osmium tags-filter <region>.osm.pbf r/admin_level=2`.

The file records the largest distance between the simplified line and the true one, measured both ways (every vertex of the true line to the simplified one, and the simplified line sampled every 10 m to the true one): `maxDeviationM`, 50.2 m today. It also records the limit the engine applies, `limitM`: 300 m less that deviation rounded up, less 1 m for the plane the engine measures on, 248 m today. A point accepted is therefore never more than 300 m outside the true border; a point between 248 and 300 m outside the simplified line may be refused, never one in a neighbouring country accepted. `--full FILE` also writes the unsimplified border, which `check --border FILE --limit 300` uses with the full 300 m.

`building-stats.py` (and through it `issue_registry.py` and `validate-grouping.py`) loads that border (`gw_codes.border()`) and drops every footprint whose centre lies beyond it, and then every compound whose centre lies beyond it, before any place or number is given; `issue_registry.py` prints how many (`abroadStructure`, `abroadCompound`). The registry server applies the same rule to every code issued on demand and every entrance moved (`422 outside`). `build_border.py check` verifies the published registry: 0 of 241,673 codes lie beyond the border, and 0 lie more than 300 m outside the unsimplified one.

## Order

```sh
python3 tools/make-sectors.py sectors-raw.geojson                  # once, before first issue
python3 tools/build_border.py build westafrica-admin.osm.pbf       # the border; again when OpenStreetMap corrects it
python3 tools/make-places.py <work>
python3 tools/gw_plates.py
python3 tools/extract-buildings.py <work>
python3 tools/building-stats.py <work>
python3 tools/issue_registry.py <work> <work>/lotes.jsonl.gz
python3 tools/export_register.py
python3 tools/vectors.py
python3 tools/build_border.py check                                # after every export of the registry
python3 tools/paper_figures.py
```
