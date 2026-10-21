#!/usr/bin/env python3
"""Extract every Guinea-Bissau building footprint with its raw profile facts.

One duckdb run (memory_limit 3GB) over N-Ways' map data, read-only:
  data/detail/countries/guinea-bissau/buildings-src.geojsonseq  OpenStreetMap buildings (ODbL)
  data/detail/ml/GW.parquet                                      Google Open Buildings / Microsoft footprints with height h (CC BY 4.0 / ODbL)
  engine/data/sectors.geojson                                    the frozen sector outlines
plus three small inputs prepared beforehand in a work folder:
  enclosures.geojson  walls, fences, hedges, landuse=farmyard (how HOT maps moranças),
                      small landuse=residential plots, sites from N-Ways' routing build
  islands.geojson     OpenStreetMap place=island/islet polygons
  places.csv          N-Ways places (POIs) inside the GW box
  gates.csv           OpenStreetMap barrier=gate points and N-Ways routing gates

Writes <work>/buildings.csv (one row per footprint, with its outline as WKT for the registry) and
<work>/enclosure-gates.csv.
  python3 tools/extract-buildings.py <work folder>
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
ROOT = os.environ.get('NWAYS_ROOT', os.path.dirname(os.path.dirname(REPO)))
work = os.path.abspath(sys.argv[1])
osm = os.path.join(ROOT, 'data', 'detail', 'countries', 'guinea-bissau', 'buildings-src.geojsonseq')
ml = os.path.join(ROOT, 'data', 'detail', 'ml', 'GW.parquet')
sectors = os.path.join(REPO, 'engine', 'data', 'sectors.geojson')
W = lambda f: os.path.join(work, f)

TAGS = ['building', 'amenity', 'shop', 'office', 'religion', 'tourism', 'healthcare', 'man_made',
        'government', 'craft', 'building:levels', 'height', 'name', 'roof:material', 'building:material']
tag_cols = ', '.join(f"json_extract_string(j, '$.properties.\"{t}\"') AS \"{t}\"" for t in TAGS)
null_cols = ', '.join(f"NULL::VARCHAR AS \"{t}\"" for t in TAGS)
utm = "ST_Transform(g, 'EPSG:4326', 'EPSG:32628', always_xy := true)"

sql = f"""
SET memory_limit='3GB'; SET threads=4; SET preserve_insertion_order=false;
INSTALL spatial; LOAD spatial;
CREATE TABLE s AS SELECT number, geom FROM ST_Read('{sectors}');
CREATE TABLE e AS SELECT eid, kind, areaM2, geom FROM ST_Read('{W('enclosures.geojson')}');
CREATE TABLE isl AS SELECT name, place, geom FROM ST_Read('{W('islands.geojson')}');
CREATE TABLE p AS SELECT id, name, category, ST_Point(lon, lat) AS g FROM read_csv('{W('places.csv')}', header=true,
  columns={{'id':'VARCHAR','name':'VARCHAR','category':'VARCHAR','source':'VARCHAR','lon':'DOUBLE','lat':'DOUBLE','building':'VARCHAR'}});
CREATE TABLE gt AS SELECT gid, src, barrier, ST_Point(lon, lat) AS g FROM read_csv('{W('gates.csv')}', header=true);
CREATE TABLE raw AS
  SELECT 'osm' AS src, json_extract_string(j, '$.properties."@type"') || '/' || json_extract_string(j, '$.properties."@id"') AS oid, ST_GeomFromGeoJSON(json_extract(j, '$.geometry')) AS g,
         NULL::DOUBLE AS h, {tag_cols}
  FROM (SELECT ltrim(line, chr(30)) AS j FROM read_csv('{osm}', columns={{'line':'VARCHAR'}}, header=false, delim=chr(1), quote='', escape='', max_line_size=16000000) WHERE length(line) > 2)
  UNION ALL
  SELECT 'ml', NULL, geometry, h, {null_cols} FROM '{ml}';
CREATE TABLE b AS SELECT row_number() OVER () AS bid, *, ST_Centroid(g) AS c, ST_Area({utm}) AS area, ST_Perimeter({utm}) AS perim,
  ST_AsText(ST_ReducePrecision(g, 0.0000001)) AS wkt FROM raw;
DROP TABLE raw;
CREATE TABLE bs AS SELECT b.bid, s.number FROM b JOIN s ON ST_Contains(s.geom, b.c);
CREATE TABLE be AS SELECT bid, arg_min(eid, areaM2) AS eid FROM (SELECT b.bid, e.eid, e.areaM2 FROM b JOIN e ON ST_Contains(e.geom, b.c)) GROUP BY bid;
CREATE TABLE bi AS SELECT bid, arg_min(name, ST_Area(geom)) AS island FROM (SELECT b.bid, isl.name, isl.geom FROM b JOIN isl ON ST_Contains(isl.geom, b.c)) GROUP BY bid;
CREATE TABLE bp AS SELECT bid, string_agg(DISTINCT category, '|') AS poi, string_agg(DISTINCT name, '|') AS poi_name
  FROM (SELECT b.bid, p.category, p.name FROM b JOIN p ON ST_Intersects(b.g, ST_Buffer(p.g, 0.00004))) GROUP BY bid;
COPY (SELECT b.bid, b.src, b.oid, round(ST_X(b.c), 7) AS lon, round(ST_Y(b.c), 7) AS lat, round(b.area, 1) AS area, round(b.perim, 1) AS perim,
        b.h, {', '.join(f'b."{t}"' for t in TAGS)}, bs.number AS sector, be.eid, bi.island, bp.poi, bp.poi_name, b.wkt
      FROM b LEFT JOIN bs USING (bid) LEFT JOIN be USING (bid) LEFT JOIN bi USING (bid) LEFT JOIN bp USING (bid))
  TO '{W('buildings.csv')}' (HEADER, DELIMITER ',');
COPY (SELECT e.eid, e.kind, e.areaM2, count(gt.gid) AS gates, round(ST_X(ST_Centroid(e.geom)),7) AS lon, round(ST_Y(ST_Centroid(e.geom)),7) AS lat
      FROM e LEFT JOIN gt ON ST_DWithin(e.geom, gt.g, 0.00005) GROUP BY ALL)
  TO '{W('enclosure-gates.csv')}' (HEADER, DELIMITER ',');
SELECT count(*), sum(CASE WHEN src='osm' THEN 1 ELSE 0 END) FROM b;
"""
r = subprocess.run(['duckdb', '-csv'], input=sql, capture_output=True, text=True)
print(r.stdout[-2000:], r.stderr[-3000:])
sys.exit(r.returncode)
