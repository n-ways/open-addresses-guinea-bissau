"""Distances, outlines and Plus Codes, with the issuer's own constants."""
import math

from .engine import ref

EARTH_M = 6371008.8  # mean Earth radius (IUGG)
M_LAT, M_LON_EQ = ref.M_LAT, ref.M_LON_EQ


def distance_m(lat1, lng1, lat2, lng2):
    """Great-circle distance in metres (used for 'a code at this point')."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_M * math.asin(min(1.0, math.sqrt(h)))


def walk_m(lat1, lng1, lat2, lng2):
    """The short-distance rule the issuer uses for a door or a moved entrance: 111,320 m per
    degree, longitude scaled at the mean latitude."""
    dy = (lat2 - lat1) * 111320
    dx = (lng2 - lng1) * 111320 * math.cos((lat1 + lat2) / 2 * math.pi / 180)
    return math.hypot(dx, dy)


def ring_open(ring):
    """An outline as [[lng, lat], ...] without the closing point."""
    r = [tuple(map(float, p)) for p in ring]
    if len(r) > 1 and r[0] == r[-1]:
        r = r[:-1]
    return r


def ring_area_m2(ring):
    """Shoelace area in square metres, longitudes scaled at the first vertex's latitude."""
    if len(ring) < 3:
        return 0.0
    k = math.cos(ring[0][1] * math.pi / 180)
    a = 0.0
    for i in range(len(ring)):
        j = (i + 1) % len(ring)
        xi, yi = ring[i][0] * M_LON_EQ * k, ring[i][1] * M_LAT
        xj, yj = ring[j][0] * M_LON_EQ * k, ring[j][1] * M_LAT
        a += xi * yj - xj * yi
    return abs(a) / 2


def ring_perimeter_m(ring):
    per = 0.0
    for i in range(len(ring)):
        j = (i + 1) % len(ring)
        per += walk_m(ring[i][1], ring[i][0], ring[j][1], ring[j][0])
    return per


def ring_box(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def in_ring(lng, lat, ring):
    return ref._in_ring(lng, lat, ring)


def _seg_m(lat, lng, a, b):
    """Distance in metres from a point to the segment a-b ([lng, lat] each), on a local plane."""
    k = math.cos(math.radians(lat))
    px, py = 0.0, 0.0
    ax, ay = (a[0] - lng) * M_LON_EQ * k, (a[1] - lat) * M_LAT
    bx, by = (b[0] - lng) * M_LON_EQ * k, (b[1] - lat) * M_LAT
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(ax + t * dx - px, ay + t * dy - py)


def ring_distance_m(lat, lng, ring):
    """0 inside the outline, else the distance to its nearest edge."""
    if in_ring(lng, lat, ring):
        return 0.0
    return min(_seg_m(lat, lng, ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring)))


def overlap_share(r1, r2, steps=80):
    """Area of the intersection of two outlines over the smaller one's area, sampled on a
    grid over the overlap of their boxes (exact enough for the issuer's 'more than half' rule)."""
    b1, b2 = ring_box(r1), ring_box(r2)
    x0, y0 = max(b1[0], b2[0]), max(b1[1], b2[1])
    x1, y1 = min(b1[2], b2[2]), min(b1[3], b2[3])
    if x0 >= x1 or y0 >= y1:
        return 0.0
    a1, a2 = ring_area_m2(r1), ring_area_m2(r2)
    if min(a1, a2) <= 0:
        return 0.0
    hits = 0
    for i in range(steps):
        x = x0 + (i + 0.5) * (x1 - x0) / steps
        for j in range(steps):
            y = y0 + (j + 0.5) * (y1 - y0) / steps
            if in_ring(x, y, r1) and in_ring(x, y, r2):
                hits += 1
    box = ring_area_m2([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    return hits / (steps * steps) * box / min(a1, a2)


_OLC = '23456789CFGHJMPQRVWX'


def plus_code(lat, lng):
    """Open Location Code of a point, 11 characters ('7C36VC23+VX4'), computed exactly as the
    issuer does (integer arithmetic on the rounded scaled coordinates)."""
    def r6(x):
        return round(x * 1e6) / 1e6
    lat = min(max(lat, -90.0), 90.0)
    lng = math.fmod(math.fmod(lng + 180, 360) + 360, 360) - 180
    lat_v = int(math.floor(r6((lat + 90) * 25000000)))
    lng_v = int(math.floor(r6((lng + 180) * 8192000)))
    if lat_v >= 180 * 25000000:
        lat_v = 180 * 25000000 - 1
    code = ''
    for _ in range(5):
        code = _OLC[(lat_v % 5) * 4 + lng_v % 4] + code
        lat_v //= 5
        lng_v //= 4
    for _ in range(5):
        code = _OLC[lng_v % 20] + code
        code = _OLC[lat_v % 20] + code
        lat_v //= 20
        lng_v //= 20
    return code[:8] + '+' + code[8:11]
