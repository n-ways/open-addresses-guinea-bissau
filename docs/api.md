# The registry API

Every endpoint of the registry server (`server/`), with a real request and the response it gave, on the full registry of 241,673 codes. The examples were taken from a server started with `python3 -m server serve` on a database imported from `registry/`, with one issuing key, and they run in the order shown: the read examples see the registry as published, and the `POST` and `PATCH` examples at the end add two codes and change them. Where a response is long, a list or a card is shortened and the text says so; nothing else is changed.

All responses are JSON (`application/json; charset=utf-8`). Errors always have the shape `{"error": {"code": "...", "message": "..."}}` with the HTTP status that fits: `400` a malformed request, `401` a missing or wrong key, `403` a read-only deployment, `404` nothing with that code or name, `405` a method not allowed, `409` a conflict (the building has a code, a retired code), `413` a body over 64 KB, `422` a well-formed request that cannot be served (a wrong check digit, a point outside the country, an outline of the wrong size), `429` the daily limit of a key. The machine-readable description is [server/openapi.yaml](../server/openapi.yaml).

In the examples the server listens on `http://localhost:8080`.

## GET /v1/health

Liveness and the registry in service: country, number of codes, the export date of the registry it was imported from, and whether this deployment issues codes.

```sh
curl -s 'http://localhost:8080/v1/health'
```

`200 OK`

```json
{
  "status": "ok",
  "country": "GW",
  "codes": 241673,
  "registry_exported": "2026-10-21T18:35:37Z",
  "issuing": true
}
```

## GET /v1/info

What this deployment serves: zones (the 39 sectors), areas, codes by status and by zone, licences, the credit line and the engine specification.

```sh
curl -s 'http://localhost:8080/v1/info'
```

`200 OK` (by_zone trimmed to 4 of 39)

```json
{
  "country": "GW",
  "name": "Guinea-Bissau",
  "zone_kind": "sector",
  "zones": 39,
  "areas": 4260,
  "codes": 241673,
  "by_status": {
    "provisional": 241673
  },
  "by_zone": {
    "BAF": 8416,
    "BAM": 6301,
    "BBQ": 2812,
    "BED": 4264
  },
  "licences": {
    "code": "Apache-2.0",
    "data": "ODbL-1.0",
    "documents": "CC-BY-4.0"
  },
  "credit": "N-Ways Addressing for Guinea-Bissau, © N-WAYS LIMITED (nways.ng)",
  "credit_url": "https://github.com/n-ways/open-addresses-guinea-bissau",
  "engine": {
    "spec": "SPEC v1.0",
    "reference": "engine/reference/gw_codes.py"
  },
  "registry_exported": "2026-10-21T18:35:37Z",
  "issuing": {
    "enabled": true,
    "per_key_per_day": 5
  }
}
```

## GET /v1/codes/{machine}

The full card of an issued code. `record` holds every registry column exactly as published; the other fields are the same values typed and named, with the area, the zone, the spot code of the entrance and the forms people use. A machine form with a structure (`.2`) or door (`/1`) suffix returns the compound's card with `structure` or `door` set. A wrong check digit is refused, never corrected.

```sh
curl -s 'http://localhost:8080/v1/codes/10-022-00537-4'
```

`200 OK`

```json
{
  "country": "GW",
  "machine": "10-022-00537-4",
  "home": "Bandim 537",
  "written": "Bandim 537",
  "spoken": "Bandim, quinhentos e trinta e sete",
  "number": 537,
  "check": 4,
  "status": "provisional",
  "issued": "bulk",
  "issued_at": "2026-10-20T06:32:58Z",
  "area": {
    "id": "BIS-022",
    "plate_name": "Bandim",
    "official_name": "Bandim",
    "kind": "neighbourhood",
    "needs_council_choice": false
  },
  "zone": {
    "key": "BIS",
    "number": 10,
    "name": "Bissau",
    "region": "GW-BS"
  },
  "full_line": "Bandim 537 · Bissau",
  "entrance": {
    "lat": 11.8521485,
    "lng": -15.5950371,
    "kind": "centre"
  },
  "spot": "10-4327-9117",
  "plus_code": "7C36VC23+VX4",
  "building": {
    "class": "residential.compound-house",
    "use": "residential",
    "kind": "building",
    "structures": 1,
    "floor_area_m2": 272.4,
    "settlement": "cidade"
  },
  "postcode": "1000",
  "record": {
    "machine": "10-022-00537-4",
    "home": "Bandim 537",
    "written": "Bandim 537",
    "area": "BIS-022",
    "official_name": "Bandim",
    "number": "537",
    "check": "4",
    "status": "provisional",
    "issued": "bulk",
    "issued_at": "2026-10-20T06:32:58Z",
    "entrance_lat": "11.8521485",
    "entrance_lng": "-15.5950371",
    "entrance_kind": "centre",
    "plus_code": "7C36VC23+VX4",
    "class": "residential.compound-house",
    "use": "residential",
    "kind": "building",
    "structures": "1",
    "floor_area_m2": "272.4",
    "settlement": "cidade",
    "postcode": "1000"
  },
  "credit": "N-Ways Addressing for Guinea-Bissau, © N-WAYS LIMITED (nways.ng)",
  "credit_url": "https://github.com/n-ways/open-addresses-guinea-bissau"
}
```

```sh
curl -s 'http://localhost:8080/v1/codes/10-022-00537-5'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "bad_check",
    "message": "The check digit does not match: a digit is wrong or two are swapped."
  }
}
```

```sh
curl -s 'http://localhost:8080/v1/codes/10-022-01999-2'
```

`404 Not Found`

```json
{
  "error": {
    "code": "not_issued",
    "message": "No compound has Bandim 1999 yet: the number is in the range of Bandim, Bissau, but unused."
  }
}
```

```sh
curl -s 'http://localhost:8080/v1/codes/99-001-00001-0'
```

`404 Not Found`

```json
{
  "error": {
    "code": "unknown_sector",
    "message": "There is no sector 99."
  }
}
```

## GET /v1/find?q=

Decodes what someone typed or said: a remembered form in any case, spacing or accents (`bandim 537`, `Bandim 537`), with an optional check digit or sector after a comma; an official name with the number; a machine form; or a spot code (the compound whose entrance is within 15 m of the spot). `kind` says which form was recognised. Cards are shortened below.

```sh
curl -s 'http://localhost:8080/v1/find?q=bandim%20%20537'
```

`200 OK` (cards shortened)

```json
{
  "query": "bandim  537",
  "kind": "remembered",
  "matches": [
    {
      "machine": "10-022-00537-4",
      "home": "Bandim 537",
      "zone": {
        "key": "BIS",
        "number": 10,
        "name": "Bissau",
        "region": "GW-BS"
      },
      "status": "provisional"
    }
  ]
}
```

```sh
curl -s 'http://localhost:8080/v1/find?q=Sinch%C3%A3%20Malam%20Baio%201'
```

`200 OK` (cards shortened)

```json
{
  "query": "Sinchã Malam Baio 1",
  "kind": "remembered",
  "matches": [
    {
      "machine": "24-148-00001-9",
      "home": "Malam Baio 1",
      "area": {
        "id": "GAL-148",
        "plate_name": "Malam Baio",
        "official_name": "Sinchã Malam Baio",
        "kind": "locality",
        "needs_council_choice": false
      }
    }
  ]
}
```

```sh
curl -s 'http://localhost:8080/v1/find?q=10-4327-8173'
```

`200 OK` (cards shortened)

```json
{
  "query": "10-4327-8173",
  "kind": "spot",
  "matches": [
    {
      "machine": "10-022-00537-4",
      "home": "Bandim 537",
      "entrance": {
        "lat": 11.8521485,
        "lng": -15.5950371,
        "kind": "centre"
      }
    }
  ]
}
```

```sh
curl -s 'http://localhost:8080/v1/find?q=Bandim%20537-9'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "bad_check",
    "message": "The check digit does not match: a digit is wrong or two are swapped."
  }
}
```

```sh
curl -s 'http://localhost:8080/v1/find?q=Bandim%202275'
```

`404 Not Found`

```json
{
  "error": {
    "code": "not_issued",
    "message": "Bandim 2275 has not been issued: the number is a spare number of that name."
  }
}
```

```sh
curl -s 'http://localhost:8080/v1/find?q=Atlantida%205'
```

`404 Not Found`

```json
{
  "error": {
    "code": "unknown_name",
    "message": "No place in Guinea-Bissau is called 'Atlantida'."
  }
}
```

## GET /v1/at?lat=&lng=

The code of the compound at a point: a recorded outline that holds the point, else the nearest live entrance within 12 m (`status: "found"`). Otherwise `status: "none"` with the zone and the area a new compound there would take, or `status: "outside"` at sea or abroad: in no sector, or more than 300 m outside the national border whatever the sector outlines say (engine/SPEC.md 3.1).

```sh
curl -s 'http://localhost:8080/v1/at?lat=11.85215&lng=-15.59504'
```

`200 OK` (card shortened)

```json
{
  "status": "found",
  "distance_m": 0,
  "code": {
    "machine": "10-022-00537-4",
    "home": "Bandim 537",
    "status": "provisional"
  },
  "zone": {
    "key": "BIS",
    "number": 10,
    "name": "Bissau",
    "region": "GW-BS"
  }
}
```

```sh
curl -s 'http://localhost:8080/v1/at?lat=11.8500&lng=-15.6200'
```

`200 OK`

```json
{
  "status": "none",
  "zone": {
    "key": "BIS",
    "number": 10,
    "name": "Bissau",
    "region": "GW-BS"
  },
  "area": {
    "id": "BIS-010",
    "plate_name": "Cuntum",
    "official_name": "Cuntum",
    "kind": "suburb",
    "needs_council_choice": false
  },
  "spot": "10-2365-9717",
  "can_issue": true
}
```

```sh
curl -s 'http://localhost:8080/v1/at?lat=11.5&lng=-16.9'
```

`200 OK`

```json
{
  "status": "outside",
  "message": "That point is not inside a sector of Guinea-Bissau."
}
```

```sh
curl -s 'http://localhost:8080/v1/at?lat=11.85'
```

`400 Bad Request`

```json
{
  "error": {
    "code": "bad_request",
    "message": "The query parameter \"lng\" is required."
  }
}
```

## GET /v1/near?lat=&lng=&radius=&limit=

Live codes whose entrance lies within `radius` metres (default 100, at most 500), nearest first, at most `limit` (default 50, at most 100).

```sh
curl -s 'http://localhost:8080/v1/near?lat=11.8521&lng=-15.5951&radius=25&limit=3'
```

`200 OK`

```json
{
  "lat": 11.8521,
  "lng": -15.5951,
  "radius_m": 25.0,
  "count": 3,
  "codes": [
    {
      "machine": "10-022-00537-4",
      "home": "Bandim 537",
      "area": "BIS-022",
      "zone": "BIS",
      "status": "provisional",
      "entrance": {
        "lat": 11.8521485,
        "lng": -15.5950371
      },
      "distance_m": 8.7
    },
    {
      "machine": "10-022-00535-8",
      "home": "Bandim 535",
      "area": "BIS-022",
      "zone": "BIS",
      "status": "provisional",
      "entrance": {
        "lat": 11.852131,
        "lng": -15.5952453
      },
      "distance_m": 16.2
    },
    {
      "machine": "10-022-00581-9",
      "home": "Bandim 581",
      "area": "BIS-022",
      "zone": "BIS",
      "status": "provisional",
      "entrance": {
        "lat": 11.8519477,
        "lng": -15.5950236
      },
      "distance_m": 18.9
    }
  ]
}
```

```sh
curl -s 'http://localhost:8080/v1/near?lat=11.8521&lng=-15.5951&radius=900'
```

`400 Bad Request`

```json
{
  "error": {
    "code": "bad_request",
    "message": "\"radius\" must be between 1 and 500."
  }
}
```

## GET /v1/verify?code=

Checks a machine code without decoding it for a person: its syntax, its check digit (which also binds the number to its area), and whether it is issued and live. Always `200`; the answer is in the fields.

```sh
curl -s 'http://localhost:8080/v1/verify?code=10-022-00537-4'
```

`200 OK`

```json
{
  "code": "10-022-00537-4",
  "syntax": true,
  "check": true,
  "issued": true,
  "valid": true,
  "status": "provisional",
  "machine": "10-022-00537-4",
  "home": "Bandim 537",
  "message": "Issued and live."
}
```

```sh
curl -s 'http://localhost:8080/v1/verify?code=10-022-00573-4'
```

`200 OK`

```json
{
  "code": "10-022-00573-4",
  "syntax": true,
  "check": false,
  "issued": false,
  "valid": false,
  "status": null,
  "machine": null,
  "home": null,
  "message": "The check digit does not match: a digit is wrong or two are swapped."
}
```

```sh
curl -s 'http://localhost:8080/v1/verify?code=10-022-01999-2'
```

`200 OK`

```json
{
  "code": "10-022-01999-2",
  "syntax": true,
  "check": true,
  "issued": false,
  "valid": false,
  "status": null,
  "machine": null,
  "home": null,
  "message": "The code is well formed and its check digit is right, but it has not been issued."
}
```

## GET /v1/spot?lat=&lng= and GET /v1/spot/decode?code=

Spot codes name any point, computed offline from the sector's grid. `spot` encodes a point (and its refinement to a third of a cell, a keypad digit); `spot/decode` returns the centre of the cell. An older spot code written with a trailing check digit is still checked.

```sh
curl -s 'http://localhost:8080/v1/spot?lat=11.8521&lng=-15.5951'
```

`200 OK`

```json
{
  "lat": 11.8521,
  "lng": -15.5951,
  "spot": "10-4327-8173",
  "refined": "10-4327-8173.1",
  "zone": {
    "key": "BIS",
    "number": 10,
    "name": "Bissau",
    "region": "GW-BS"
  },
  "cell_m": 1.7,
  "refined_cell_m": 0.57
}
```

```sh
curl -s 'http://localhost:8080/v1/spot/decode?code=10-4327-8173.1'
```

`200 OK`

```json
{
  "code": "10-4327-8173.1",
  "zone": {
    "key": "BIS",
    "number": 10,
    "name": "Bissau",
    "region": "GW-BS"
  },
  "lat": 11.8520977,
  "lng": -15.5950989,
  "cell_m": 0.57
}
```

```sh
curl -s 'http://localhost:8080/v1/spot/decode?code=10-4327-8173-4'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "bad_check",
    "message": "The check digit does not match: a digit is wrong or two are swapped."
  }
}
```

```sh
curl -s 'http://localhost:8080/v1/spot?lat=11.5&lng=-16.9'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "outside",
    "message": "That point is not inside a sector of Guinea-Bissau."
  }
}
```

## GET /v1/zones and GET /v1/zones/{key}

The 39 sectors with their counts; one sector by key (`KOM`) or number (`94`), with its spot grid and every area: blocks, names and number of codes. Lists are shortened below.

```sh
curl -s 'http://localhost:8080/v1/zones'
```

`200 OK` (3 of 39 zones shown)

```json
{
  "country": "GW",
  "zone_kind": "sector",
  "zones": [
    {
      "key": "BIS",
      "number": 10,
      "name": "Bissau",
      "region": "GW-BS",
      "areas": 73,
      "codes": 43850
    },
    {
      "key": "BAF",
      "number": 21,
      "name": "Bafatá",
      "region": "GW-BA",
      "areas": 120,
      "codes": 8416
    },
    {
      "key": "BAM",
      "number": 22,
      "name": "Bambadinca",
      "region": "GW-BA",
      "areas": 139,
      "codes": 6301
    }
  ]
}
```

```sh
curl -s 'http://localhost:8080/v1/zones/KOM'
```

`200 OK` (2 of 27 areas shown)

```json
{
  "key": "KOM",
  "number": 94,
  "name": "Komo",
  "region": "GW-TO",
  "codes": 750,
  "grid": {
    "lon0": -15.408,
    "lat0": 11.104,
    "phi0": 11.19,
    "cellMetres": 2.4
  },
  "areas": [
    {
      "id": "KOM-000",
      "plate_name": "Komo",
      "official_name": "Komo",
      "kind": "sector",
      "needs_council_choice": false,
      "zone": "KOM",
      "name_key": "kumu",
      "name_id": 1812,
      "blocks": [
        [
          500,
          599
        ]
      ],
      "aliases": [],
      "landmass": null,
      "lat": null,
      "lon": null,
      "codes": 24
    },
    {
      "id": "KOM-001",
      "plate_name": "Tabanca Velha",
      "official_name": "Tabanca Velha",
      "kind": "locality",
      "needs_council_choice": true,
      "zone": "KOM",
      "name_key": "vila",
      "name_id": 3233,
      "blocks": [
        [
          0,
          99
        ]
      ],
      "aliases": [],
      "landmass": "Ilha de Caiar",
      "lat": 11.18333,
      "lon": -15.38333,
      "codes": 22
    }
  ]
}
```

```sh
curl -s 'http://localhost:8080/v1/zones/XYZ'
```

`404 Not Found`

```json
{
  "error": {
    "code": "not_found",
    "message": "There is no zone 'XYZ'. GET /v1/zones lists them."
  }
}
```

## GET /v1/zones/{key}/codes?after=&limit=

Every code of a sector, in machine-code order, `limit` per page (default 100, at most 1000). Pass the `next` value as `after` to get the next page; `next` is `null` on the last page.

```sh
curl -s 'http://localhost:8080/v1/zones/KOM/codes?limit=3'
```

`200 OK`

```json
{
  "zone": "KOM",
  "after": null,
  "count": 3,
  "codes": [
    {
      "machine": "94-000-00501-2",
      "home": "Komo 501",
      "area": "KOM-000",
      "zone": "KOM",
      "status": "provisional",
      "entrance": {
        "lat": 11.1628014,
        "lng": -15.3479258
      }
    },
    {
      "machine": "94-000-00503-6",
      "home": "Komo 503",
      "area": "KOM-000",
      "zone": "KOM",
      "status": "provisional",
      "entrance": {
        "lat": 11.1634972,
        "lng": -15.3479932
      }
    },
    {
      "machine": "94-000-00505-7",
      "home": "Komo 505",
      "area": "KOM-000",
      "zone": "KOM",
      "status": "provisional",
      "entrance": {
        "lat": 11.1637876,
        "lng": -15.3463083
      }
    }
  ],
  "next": "94-000-00505-7"
}
```

## GET /v1/areas/{id} and GET /v1/areas?name=

One area with its blocks, names, counts by status, the other areas that share its name (and so its national number range) and the name's high-water mark. `?name=` finds areas by plate name, official name or alias, folded the way the engine folds names.

```sh
curl -s 'http://localhost:8080/v1/areas/BIS-022'
```

`200 OK`

```json
{
  "id": "BIS-022",
  "plate_name": "Bandim",
  "official_name": "Bandim",
  "kind": "neighbourhood",
  "needs_council_choice": false,
  "zone": {
    "key": "BIS",
    "number": 10,
    "name": "Bissau",
    "region": "GW-BS"
  },
  "name_key": "bandim",
  "name_id": 228,
  "blocks": [
    [
      0,
      1999
    ]
  ],
  "aliases": [],
  "landmass": "Ilha de Bissau",
  "lat": 11.8521,
  "lon": -15.59506,
  "codes": {
    "total": 452,
    "by_status": {
      "provisional": 452
    }
  },
  "same_name": [
    "CAT-005"
  ],
  "next_free_after": 2200
}
```

```sh
curl -s 'http://localhost:8080/v1/areas?name=missira'
```

`200 OK` (2 of the areas shown)

```json
{
  "name": "missira",
  "name_key": "misira",
  "count": 19,
  "areas": [
    {
      "id": "BAF-010",
      "plate_name": "Missirá",
      "official_name": "Missirá",
      "kind": "locality",
      "needs_council_choice": false,
      "zone": "BAF",
      "name_key": "misira",
      "name_id": 2098,
      "blocks": [],
      "aliases": [],
      "landmass": null,
      "lat": 12.16667,
      "lon": -14.66667,
      "codes": 0
    },
    {
      "id": "BAF-092",
      "plate_name": "Missirá",
      "official_name": "Missirá",
      "kind": "locality",
      "needs_council_choice": false,
      "zone": "BAF",
      "name_key": "misira",
      "name_id": 2098,
      "blocks": [
        [
          6000,
          6199
        ]
      ],
      "aliases": [],
      "landmass": null,
      "lat": 12.28333,
      "lon": -14.5,
      "codes": 49
    }
  ]
}
```

```sh
curl -s 'http://localhost:8080/v1/areas/BIS-999'
```

`404 Not Found`

```json
{
  "error": {
    "code": "not_found",
    "message": "There is no area 'BIS-999'. Area ids look like BIS-022."
  }
}
```

## POST /v1/codes

Issues a code for a new compound, or for another door of a compound (`of`), by the issuer's rules (server/README.md). Requires `Authorization: Bearer <key>` with a key from `ISSUE_KEYS`; a deployment without keys answers `403 read_only`. Body: `{"lat", "lng", "outline"?: [[lng, lat], ...], "of"?: "<machine>"}`. A building that already has a code gets `409 exists` with that code's card. A point in no sector, or more than 300 m outside the national border whatever the sector outlines say (engine/SPEC.md 3.1), gets `422 outside`. Each key may issue `ISSUE_PER_DAY` codes in any 24 hours (`429 rate_limited`).

```sh
curl -s -X POST -H "Authorization: Bearer $ISSUE_KEY" -H "Content-Type: application/json" -d '{"lat": 11.8667292, "lng": -15.6004729}' 'http://localhost:8080/v1/codes'
```

`201 Created`

```json
{
  "country": "GW",
  "machine": "10-049-00240-4",
  "home": "Granja 240",
  "written": "Granja 240",
  "spoken": "Granja, duzentos e quarenta",
  "number": 240,
  "check": 4,
  "status": "provisional",
  "issued": "on-demand",
  "issued_at": "2026-10-21T19:04:23Z",
  "area": {
    "id": "BIS-049",
    "plate_name": "Granja",
    "official_name": "Granja",
    "kind": "neighbourhood",
    "needs_council_choice": false
  },
  "zone": {
    "key": "BIS",
    "number": 10,
    "name": "Bissau",
    "region": "GW-BS"
  },
  "full_line": "Granja 240 · Bissau",
  "entrance": {
    "lat": 11.8667292,
    "lng": -15.6004729,
    "kind": "centre"
  },
  "spot": "10-3496-4625",
  "plus_code": "7C36V98X+MRR",
  "building": {
    "class": null,
    "use": "residential",
    "kind": "building",
    "structures": 0,
    "floor_area_m2": 0.0,
    "settlement": null
  },
  "postcode": "1000",
  "record": {
    "machine": "10-049-00240-4",
    "home": "Granja 240",
    "written": "Granja 240",
    "area": "BIS-049",
    "official_name": "Granja",
    "number": "240",
    "check": "4",
    "status": "provisional",
    "issued": "on-demand",
    "issued_at": "2026-10-21T19:04:23Z",
    "entrance_lat": "11.8667292",
    "entrance_lng": "-15.6004729",
    "entrance_kind": "centre",
    "plus_code": "7C36V98X+MRR",
    "class": "",
    "use": "residential",
    "kind": "building",
    "structures": "0",
    "floor_area_m2": "0.0",
    "settlement": "",
    "postcode": "1000"
  },
  "credit": "N-Ways Addressing for Guinea-Bissau, © N-WAYS LIMITED (nways.ng)",
  "credit_url": "https://github.com/n-ways/open-addresses-guinea-bissau"
}
```

```sh
curl -s -X POST -H "Authorization: Bearer $ISSUE_KEY" -H "Content-Type: application/json" -d '{"lat": 11.8667292, "lng": -15.6004729}' 'http://localhost:8080/v1/codes'
```

`409 Conflict` (card shortened)

```json
{
  "error": {
    "code": "exists",
    "message": "This building already has its code: Granja 240.",
    "card": {
      "machine": "10-049-00240-4",
      "home": "Granja 240"
    }
  }
}
```

```sh
curl -s -X POST -H "Authorization: Bearer $ISSUE_KEY" -H "Content-Type: application/json" -d '{"lat": 11.8667292, "lng": -15.6002729, "of": "10-049-00240-4"}' 'http://localhost:8080/v1/codes'
```

`201 Created` (card shortened)

```json
{
  "machine": "10-049-00718-6",
  "home": "Granja 718",
  "area": {
    "id": "BIS-049",
    "plate_name": "Granja",
    "official_name": "Granja",
    "kind": "neighbourhood",
    "needs_council_choice": false
  },
  "entrance": {
    "lat": 11.8667292,
    "lng": -15.6002729,
    "kind": "door"
  },
  "status": "provisional",
  "issued": "on-demand"
}
```

```sh
curl -s -X POST -H "Authorization: Bearer $ISSUE_KEY" -H "Content-Type: application/json" -d '{"lat": 11.5, "lng": -16.9}' 'http://localhost:8080/v1/codes'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "outside",
    "message": "That point is outside Guinea-Bissau, so it cannot have a Guinea-Bissau code."
  }
}
```

```sh
curl -s -X POST -H "Content-Type: application/json" -d '{"lat": 11.8667292, "lng": -15.6004729}' 'http://localhost:8080/v1/codes'
```

`401 Unauthorized`

```json
{
  "error": {
    "code": "unauthorized",
    "message": "Send the issuing key as \"Authorization: Bearer <key>\"."
  }
}
```

```sh
curl -s -X POST -H "Authorization: Bearer $ISSUE_KEY" -H "Content-Type: application/json" -d '{"lat": 11.8667292, "lng": -15.6004729}' 'http://localhost:8080/v1/codes'
```

`403 Forbidden` (a deployment started without ISSUE_KEYS)

```json
{
  "error": {
    "code": "read_only",
    "message": "This deployment is read-only: it does not issue or change codes."
  }
}
```

## PATCH /v1/codes/{machine}

Changes a code's status (`provisional`, `confirmed`, `retired`) or moves its entrance by at most 80 m, never to a point outside Guinea-Bissau (`422 outside`, as for `POST /v1/codes`). A retired code is final: its number is never reused. Requires an issuing key.

```sh
curl -s -X PATCH -H "Authorization: Bearer $ISSUE_KEY" -H "Content-Type: application/json" -d '{"status": "confirmed"}' 'http://localhost:8080/v1/codes/10-049-00240-4'
```

`200 OK` (card shortened)

```json
{
  "machine": "10-049-00240-4",
  "home": "Granja 240",
  "status": "confirmed"
}
```

```sh
curl -s -X PATCH -H "Authorization: Bearer $ISSUE_KEY" -H "Content-Type: application/json" -d '{"entrance": {"lat": 11.8668292, "lng": -15.6004729}}' 'http://localhost:8080/v1/codes/10-049-00240-4'
```

`200 OK` (card shortened)

```json
{
  "machine": "10-049-00240-4",
  "entrance": {
    "lat": 11.8668292,
    "lng": -15.6004729,
    "kind": "gate"
  },
  "plus_code": "7C36V98X+PRJ"
}
```

```sh
curl -s -X PATCH -H "Authorization: Bearer $ISSUE_KEY" -H "Content-Type: application/json" -d '{"entrance": {"lat": 11.8767292, "lng": -15.6004729}}' 'http://localhost:8080/v1/codes/10-049-00240-4'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "too_far",
    "message": "The new entrance is 1102 m away; an entrance moves at most 80 m."
  }
}
```

```sh
curl -s -X PATCH -H "Authorization: Bearer $ISSUE_KEY" -H "Content-Type: application/json" -d '{"status": "retired"}' 'http://localhost:8080/v1/codes/10-049-00240-4'
```

`200 OK` (card shortened)

```json
{
  "machine": "10-049-00240-4",
  "status": "retired"
}
```

```sh
curl -s -X PATCH -H "Authorization: Bearer $ISSUE_KEY" -H "Content-Type: application/json" -d '{"status": "confirmed"}' 'http://localhost:8080/v1/codes/10-049-00240-4'
```

`409 Conflict`

```json
{
  "error": {
    "code": "retired",
    "message": "Granja 240 is retired; a retired code is never brought back or reused."
  }
}
```
