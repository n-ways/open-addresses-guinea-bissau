"""SQLite storage: import of the published registry, export in the same format, queries.

Every registry column is kept as the exact text of the published CSV, so an export of an
unchanged database reproduces the published files byte for byte. Typed copies of the
columns a query needs (number, coordinates, name number) sit beside them.
"""
import csv
import datetime
import glob
import gzip
import hashlib
import io
import json
import math
import os
import sqlite3
import threading

from .engine import COUNTRY, CREDIT, Register

CODE_COLUMNS = ['machine', 'home', 'written', 'area', 'official_name', 'number', 'check', 'status', 'issued', 'issued_at',
                'entrance_lat', 'entrance_lng', 'entrance_kind', 'plus_code', 'class', 'use', 'kind', 'structures',
                'floor_area_m2', 'settlement', 'postcode']
AREA_COLUMNS = ['area', 'sector', 'index', 'sector_key', 'plate_name', 'official_name', 'kind', 'name_key', 'name_id',
                'blocks', 'needs_council_choice', 'aliases', 'landmass', 'lat', 'lon']
GRID = 0.001  # degrees per cell of the fallback spatial index (about 110 m)

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS areas (
  ord INTEGER NOT NULL, area TEXT PRIMARY KEY, sector TEXT, "index" TEXT, sector_key TEXT, plate_name TEXT,
  official_name TEXT, kind TEXT, name_key TEXT, name_id TEXT, blocks TEXT, needs_council_choice TEXT, aliases TEXT,
  landmass TEXT, lat TEXT, lon TEXT);
CREATE TABLE IF NOT EXISTS codes (
  id INTEGER PRIMARY KEY,
  machine TEXT NOT NULL UNIQUE, home TEXT, written TEXT, area TEXT, official_name TEXT, number TEXT, "check" TEXT,
  status TEXT, issued TEXT, issued_at TEXT, entrance_lat TEXT, entrance_lng TEXT, entrance_kind TEXT, plus_code TEXT,
  class TEXT, use TEXT, kind TEXT, structures TEXT, floor_area_m2 TEXT, settlement TEXT, postcode TEXT,
  zone TEXT NOT NULL, name_id INTEGER NOT NULL, num INTEGER NOT NULL,
  lat REAL NOT NULL, lng REAL NOT NULL, anchor_lat REAL NOT NULL, anchor_lng REAL NOT NULL,
  home_key TEXT NOT NULL, official_key TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS codes_home ON codes (home_key);
CREATE INDEX IF NOT EXISTS codes_official ON codes (official_key, num);
CREATE INDEX IF NOT EXISTS codes_zone ON codes (zone, machine);
CREATE INDEX IF NOT EXISTS codes_area ON codes (area, num);
CREATE UNIQUE INDEX IF NOT EXISTS codes_name_number ON codes (name_id, num);
CREATE TABLE IF NOT EXISTS outlines (machine TEXT PRIMARY KEY, ring TEXT NOT NULL,
  min_lat REAL, max_lat REAL, min_lng REAL, max_lng REAL);
CREATE TABLE IF NOT EXISTS issue_log (id INTEGER PRIMARY KEY, key_id TEXT NOT NULL, machine TEXT NOT NULL, at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS issue_log_key ON issue_log (key_id, at);
"""


def text_key(s):
    """Case, accents and spacing folded: how a typed form is matched against the index."""
    from .engine import ref
    return ' '.join(ref.plain(s or '').split())


class RegistryError(Exception):
    pass


def has_rtree(con):
    try:
        con.execute('CREATE VIRTUAL TABLE IF NOT EXISTS temp._rt_probe USING rtree(id, a, b, c, d)')
        con.execute('DROP TABLE temp._rt_probe')
        return True
    except sqlite3.OperationalError:
        return False


def connect(path):
    con = sqlite3.connect(path, timeout=30, isolation_level=None, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA synchronous=NORMAL')
    con.execute('PRAGMA foreign_keys=ON')
    return con


# ---------------------------------------------------------------------- CSV, as the issuer writes it

def _needs_quotes(field):
    if field == '':
        return False
    if field == '\\.' or any(c in field for c in ',"\r\n'):
        return True
    return field[0].isspace()


def csv_line(fields):
    """One CSV record as the issuer writes it: quoted only when needed, '\\n' line ends."""
    out = []
    for f in fields:
        out.append('"' + f.replace('"', '""') + '"' if _needs_quotes(f) else f)
    return ','.join(out) + '\n'


class _HashedLines:
    """Lines of a gzip CSV, decoded, while the SHA-256 of the uncompressed bytes is taken."""

    def __init__(self, path):
        self.f = gzip.open(path, 'rb')
        self.sha = hashlib.sha256()

    def __iter__(self):
        for raw in self.f:
            self.sha.update(raw)
            yield raw.decode('utf-8')

    def close(self):
        self.f.close()


# ---------------------------------------------------------------------- import

def import_registry(registry, db_path, force=False, log=print):
    """Load every registry/*.csv.gz into a fresh database at db_path. Each file's SHA-256
    and row count must match MANIFEST.json, or nothing is replaced. A database that holds
    codes issued since its import is kept unless force is set: replacing it would forget
    numbers already handed out."""
    man_path = os.path.join(registry, 'MANIFEST.json')
    with open(man_path, encoding='utf-8') as f:
        manifest = json.load(f)
    if manifest.get('country') != COUNTRY:
        raise RegistryError(f'{man_path} is for country {manifest.get("country")!r}, not {COUNTRY}')
    if os.path.exists(db_path) and not force:
        old = connect(db_path)
        try:
            n = old.execute("SELECT count(*) FROM codes WHERE issued = 'on-demand'").fetchone()[0]
            changed = old.execute("SELECT value FROM meta WHERE key = 'changed'").fetchone()
        except sqlite3.OperationalError:
            n, changed = 0, None
        finally:
            old.close()
        if n or (changed and changed[0] == '1'):
            raise RegistryError(f'{db_path} holds {n} codes issued here and other changes since its import; '
                                'export them first, or pass --force to replace the database')
    tmp = db_path + '.importing'
    for p in (tmp, tmp + '-wal', tmp + '-shm'):
        if os.path.exists(p):
            os.remove(p)
    con = connect(tmp)
    try:
        con.executescript(SCHEMA)
        rtree = has_rtree(con)
        con.execute('BEGIN')
        areas_path = os.path.join(registry, 'areas.csv.gz')
        lines = _HashedLines(areas_path)
        rd = csv.reader(lines)
        header = next(rd)
        if header != AREA_COLUMNS:
            raise RegistryError(f'{areas_path}: unexpected columns {header}')
        rows = []
        for k, r in enumerate(rd):
            rows.append(r)
            con.execute('INSERT INTO areas VALUES (?,' + ','.join('?' * len(AREA_COLUMNS)) + ')', [k] + r)
        lines.close()
        _check_sha(manifest, 'areas.csv', lines.sha.hexdigest())
        name_ids = {r[0]: int(r[8]) for r in rows}
        total = 0
        files = sorted(glob.glob(os.path.join(registry, '*.csv.gz')))
        zones = [os.path.basename(p)[:-7] for p in files if os.path.basename(p) != 'areas.csv.gz']
        if sorted(zones) != sorted(manifest.get('bySector', {})):
            raise RegistryError(f'zone files {sorted(zones)} do not match the manifest {sorted(manifest.get("bySector", {}))}')
        for zone in zones:
            path = os.path.join(registry, zone + '.csv.gz')
            lines = _HashedLines(path)
            rd = csv.reader(lines)
            header = next(rd)
            if header != CODE_COLUMNS:
                raise RegistryError(f'{path}: unexpected columns {header}')
            n = 0
            batch = []
            for r in rd:
                if len(r) != len(CODE_COLUMNS):
                    raise RegistryError(f'{path}: a row has {len(r)} fields: {r[:1]}')
                lat, lng = float(r[10]), float(r[11])
                nid = name_ids.get(r[3])
                if nid is None:
                    raise RegistryError(f'{path}: {r[0]} is in area {r[3]}, which is not in areas.csv')
                batch.append(r + [zone, nid, int(r[5]), lat, lng, lat, lng, text_key(r[1]), text_key(r[4])])
                n += 1
                if len(batch) >= 5000:
                    _insert_codes(con, batch)
                    batch = []
            _insert_codes(con, batch)
            lines.close()
            _check_sha(manifest, zone + '.csv', lines.sha.hexdigest())
            want = manifest['bySector'][zone]
            if n != want:
                raise RegistryError(f'{zone}: {n} rows, the manifest says {want}')
            total += n
            log(f'  {zone}: {n} codes')
        if total != manifest['codes']:
            raise RegistryError(f'{total} codes in the files, the manifest says {manifest["codes"]}')
        _build_spatial(con, rtree)
        meta = {'country': COUNTRY, 'exported': manifest.get('exported', ''), 'manifest': json.dumps(manifest),
                'imported': _now(), 'changed': '0', 'spatial': 'rtree' if rtree else 'grid'}
        con.executemany('INSERT OR REPLACE INTO meta VALUES (?, ?)', list(meta.items()))
        con.execute('COMMIT')
        con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        con.execute('ANALYZE')
    except BaseException:
        con.close()
        for p in (tmp, tmp + '-wal', tmp + '-shm'):
            if os.path.exists(p):
                os.remove(p)
        raise
    con.close()
    for p in (db_path + '-wal', db_path + '-shm'):
        if os.path.exists(p):
            os.remove(p)
    os.replace(tmp, db_path)
    return total


def _check_sha(manifest, name, got):
    want = manifest.get('sha256', {}).get(name)
    if want != got:
        raise RegistryError(f'{name}: SHA-256 {got} does not match the manifest ({want})')


def _insert_codes(con, batch):
    if batch:
        con.executemany('INSERT INTO codes (' + ','.join('"%s"' % c for c in CODE_COLUMNS) +
                        ', zone, name_id, num, lat, lng, anchor_lat, anchor_lng, home_key, official_key) VALUES (' +
                        ','.join('?' * (len(CODE_COLUMNS) + 9)) + ')', batch)


def _build_spatial(con, rtree):
    if rtree:
        con.execute('CREATE VIRTUAL TABLE IF NOT EXISTS codes_rt USING rtree(id, min_lat, max_lat, min_lng, max_lng)')
        con.execute('INSERT INTO codes_rt SELECT id, lat, lat, lng, lng FROM codes')
    else:
        con.execute('CREATE TABLE IF NOT EXISTS codes_grid (cy INTEGER, cx INTEGER, id INTEGER)')
        con.execute('CREATE INDEX IF NOT EXISTS codes_grid_cell ON codes_grid (cy, cx)')
        for row in con.execute('SELECT id, lat, lng FROM codes').fetchall():
            con.execute('INSERT INTO codes_grid VALUES (?,?,?)', (math.floor(row[1] / GRID), math.floor(row[2] / GRID), row[0]))


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# ---------------------------------------------------------------------- export

def export_registry(db_path, out):
    """Write the registry in the published format: one <ZONE>.csv.gz per sector with codes,
    areas.csv.gz (and areas.csv), MANIFEST.json. Gzip without name or time (gzip -n). An
    unchanged database keeps its export date, so its whole export is byte-identical."""
    con = connect(db_path)
    try:
        os.makedirs(out, exist_ok=True)
        meta = dict(con.execute('SELECT key, value FROM meta').fetchall())
        manifest = json.loads(meta['manifest'])
        shas, counts = {}, {}

        def write(name, header, rows):
            sha = hashlib.sha256()
            path = os.path.join(out, name + '.gz')
            with open(path, 'wb') as raw:
                with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=9) as gz:
                    for fields in _chain(header, rows):
                        b = csv_line(fields).encode('utf-8')
                        sha.update(b)
                        gz.write(b)
            shas[name] = sha.hexdigest()

        area_rows = [list(r) for r in con.execute('SELECT ' + ','.join('"%s"' % c for c in AREA_COLUMNS) +
                                                   ' FROM areas ORDER BY ord')]
        write('areas.csv', AREA_COLUMNS, area_rows)
        with open(os.path.join(out, 'areas.csv'), 'wb') as f:
            f.write(b''.join(csv_line(r).encode('utf-8') for r in [AREA_COLUMNS] + area_rows))
        total = 0
        reg = Register([dict(zip(AREA_COLUMNS, r)) for r in area_rows])
        for number in sorted(reg.sectors):
            key = reg.sectors[number]['key']
            n = con.execute('SELECT count(*) FROM codes WHERE zone = ?', (key,)).fetchone()[0]
            if not n:
                continue
            cur = con.execute('SELECT ' + ','.join('"%s"' % c for c in CODE_COLUMNS) +
                              ' FROM codes WHERE zone = ? ORDER BY name_id, num', (key,))
            write(key + '.csv', CODE_COLUMNS, (list(r) for r in cur))
            counts[key] = n
            total += n
        exported = meta['exported'] if meta.get('changed') == '0' and meta.get('exported') else _now()
        man = {'country': COUNTRY, 'engine': manifest.get('engine', 'internal/addressing/gw (SPEC v1.0)'),
               'exported': exported, 'codes': total, 'bySector': counts, 'sha256': shas,
               'credit': manifest.get('credit', CREDIT), 'licence': manifest.get('licence', 'ODbL 1.0 (LICENSE-DATA)')}
        with open(os.path.join(out, 'MANIFEST.json'), 'w', encoding='utf-8') as f:
            f.write(json.dumps(man, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
        return total
    finally:
        con.close()


def _chain(header, rows):
    yield header
    for r in rows:
        yield r


# ---------------------------------------------------------------------- the running store

class Store:
    """Thread-safe access for the HTTP server: one connection per thread, one writer."""

    def __init__(self, path):
        if not os.path.exists(path):
            raise RegistryError(f'no database at {path}: run `python3 -m server import` first')
        self.path = path
        self.local = threading.local()
        self.write_lock = threading.Lock()
        self._all = []
        con = self.con()
        meta = dict(con.execute('SELECT key, value FROM meta').fetchall())
        if meta.get('country') != COUNTRY:
            raise RegistryError(f'{path} is not a {COUNTRY} registry database')
        self.meta = meta
        self.spatial = meta.get('spatial', 'grid')
        self.register = Register(self.area_rows())

    def con(self):
        c = getattr(self.local, 'con', None)
        if c is None:
            c = self.local.con = connect(self.path)
            self._all.append(c)
        return c

    def close(self):
        for c in self._all:
            c.close()
        self._all = []
        self.local = threading.local()

    def area_rows(self):
        return [dict(zip(AREA_COLUMNS, r)) for r in self.con().execute(
            'SELECT ' + ','.join('"%s"' % c for c in AREA_COLUMNS) + ' FROM areas ORDER BY ord')]

    def manifest(self):
        return json.loads(self.meta['manifest'])

    # -------------------------------------------------------------- reads

    def by_machine(self, machine):
        return self.con().execute('SELECT * FROM codes WHERE machine = ?', (machine,)).fetchone()

    def by_area_number(self, area, number):
        return self.con().execute('SELECT * FROM codes WHERE area = ? AND num = ?', (area, number)).fetchone()

    def by_official(self, official_key, number):
        return self.con().execute('SELECT * FROM codes WHERE official_key = ? AND num = ?', (official_key, number)).fetchall()

    def count(self):
        return self.con().execute('SELECT count(*) FROM codes').fetchone()[0]

    def counts_by_zone(self):
        return dict(self.con().execute('SELECT zone, count(*) FROM codes GROUP BY zone').fetchall())

    def counts_by_status(self):
        return dict(self.con().execute('SELECT status, count(*) FROM codes GROUP BY status').fetchall())

    def counts_by_area(self, zone=None):
        if zone:
            q = self.con().execute('SELECT area, count(*) FROM codes WHERE zone = ? GROUP BY area', (zone,))
        else:
            q = self.con().execute('SELECT area, count(*) FROM codes GROUP BY area')
        return dict(q.fetchall())

    def area_status(self, area):
        return dict(self.con().execute('SELECT status, count(*) FROM codes WHERE area = ? GROUP BY status', (area,)).fetchall())

    def area_numbers(self, area):
        """Every number an area holds, retired ones too, with the point its order is taken from."""
        return [(r[0], r[1], r[2]) for r in self.con().execute(
            'SELECT num, anchor_lat, anchor_lng FROM codes WHERE area = ?', (area,))]

    def zone_page(self, zone, after, limit):
        return self.con().execute('SELECT * FROM codes WHERE zone = ? AND machine > ? ORDER BY machine LIMIT ?',
                                  (zone, after, limit)).fetchall()

    def within(self, lat, lng, radius_m, live_only=True):
        """Codes whose entrance lies within radius_m of the point: (distance, row), nearest first."""
        from .geo import distance_m
        dlat = radius_m / 110574.0 + 1e-6
        dlng = radius_m / (111320.0 * max(0.01, math.cos(math.radians(lat)))) + 1e-6
        if self.spatial == 'rtree':
            rows = self.con().execute(
                'SELECT c.* FROM codes_rt r JOIN codes c ON c.id = r.id WHERE r.min_lat <= ? AND r.max_lat >= ? '
                'AND r.min_lng <= ? AND r.max_lng >= ?', (lat + dlat, lat - dlat, lng + dlng, lng - dlng)).fetchall()
        else:
            y0, y1 = math.floor((lat - dlat) / GRID), math.floor((lat + dlat) / GRID)
            x0, x1 = math.floor((lng - dlng) / GRID), math.floor((lng + dlng) / GRID)
            rows = self.con().execute(
                'SELECT c.* FROM codes_grid g JOIN codes c ON c.id = g.id WHERE g.cy BETWEEN ? AND ? AND g.cx BETWEEN ? AND ?',
                (y0, y1, x0, x1)).fetchall()
        out = []
        for r in rows:
            if live_only and r['status'] == 'retired':
                continue
            d = distance_m(lat, lng, r['lat'], r['lng'])
            if d <= radius_m:
                out.append((d, r))
        out.sort(key=lambda t: (t[0], t[1]['machine']))
        return out

    def outlines_near(self, lat, lng, pad_deg=0.002):
        return self.con().execute(
            'SELECT o.machine, o.ring FROM outlines o JOIN codes c ON c.machine = o.machine WHERE c.status <> \'retired\' '
            'AND o.min_lat <= ? AND o.max_lat >= ? AND o.min_lng <= ? AND o.max_lng >= ?',
            (lat + pad_deg, lat - pad_deg, lng + pad_deg, lng - pad_deg)).fetchall()

    def outline_of(self, machine):
        r = self.con().execute('SELECT ring FROM outlines WHERE machine = ?', (machine,)).fetchone()
        return json.loads(r[0]) if r else None

    def issued_since(self, key_id, since):
        return self.con().execute('SELECT count(*) FROM issue_log WHERE key_id = ? AND at >= ?', (key_id, since)).fetchone()[0]

    # -------------------------------------------------------------- writes (callers hold write_lock)

    def insert_code(self, con, rec, zone, name_id, num, lat, lng, ring, new_block_area, key_id, now):
        con.execute('INSERT INTO codes (' + ','.join('"%s"' % c for c in CODE_COLUMNS) +
                    ', zone, name_id, num, lat, lng, anchor_lat, anchor_lng, home_key, official_key) VALUES (' +
                    ','.join('?' * (len(CODE_COLUMNS) + 9)) + ')',
                    [rec[c] for c in CODE_COLUMNS] + [zone, name_id, num, lat, lng, lat, lng,
                                                      text_key(rec['home']), text_key(rec['official_name'])])
        rid = con.execute('SELECT id FROM codes WHERE machine = ?', (rec['machine'],)).fetchone()[0]
        self._index_point(con, rid, lat, lng)
        if ring:
            from .geo import ring_box
            x0, y0, x1, y1 = ring_box(ring)
            con.execute('INSERT INTO outlines VALUES (?,?,?,?,?,?)', (rec['machine'], json.dumps(ring), y0, y1, x0, x1))
        if new_block_area is not None:
            con.execute('UPDATE areas SET blocks = ? WHERE area = ?', new_block_area)
        con.execute('INSERT INTO issue_log (key_id, machine, at) VALUES (?,?,?)', (key_id, rec['machine'], now))
        con.execute("INSERT OR REPLACE INTO meta VALUES ('changed', '1')")

    def _index_point(self, con, rid, lat, lng):
        if self.spatial == 'rtree':
            con.execute('INSERT OR REPLACE INTO codes_rt VALUES (?,?,?,?,?)', (rid, lat, lat, lng, lng))
        else:
            con.execute('DELETE FROM codes_grid WHERE id = ?', (rid,))
            con.execute('INSERT INTO codes_grid VALUES (?,?,?)', (math.floor(lat / GRID), math.floor(lng / GRID), rid))

    def set_status(self, con, machine, status):
        con.execute('UPDATE codes SET status = ? WHERE machine = ?', (status, machine))
        con.execute("INSERT OR REPLACE INTO meta VALUES ('changed', '1')")

    def set_entrance(self, con, row, lat, lng, plus):
        con.execute('UPDATE codes SET entrance_lat = ?, entrance_lng = ?, entrance_kind = ?, plus_code = ?, lat = ?, lng = ? '
                    'WHERE machine = ?', ('%.7f' % lat, '%.7f' % lng, 'gate', plus, lat, lng, row['machine']))
        self._index_point(con, row['id'], lat, lng)
        con.execute("INSERT OR REPLACE INTO meta VALUES ('changed', '1')")


def gzip_text(path):
    """The uncompressed text of a .gz file (tests and checks)."""
    with gzip.open(path, 'rb') as f:
        return io.TextIOWrapper(f, encoding='utf-8', newline='').read()
