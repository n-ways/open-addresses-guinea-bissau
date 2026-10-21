# Contributing

Corrections and proposals are welcome from anyone: residents, municipal and national bodies, researchers, couriers and developers. This repository holds the model, the engine, the registry, the server and the paper of N-Ways Addressing for Guinea-Bissau; [GOVERNANCE.md](GOVERNANCE.md) says what may change and how.

## What to send, and where

| You want to | Do this |
|---|---|
| Correct a place name, propose a plate name for a flagged place, report a compound with the wrong code or a missing one | open an issue with the code (`Bandim 537` or `10-022-00537-4`), what is wrong and, where you have it, a source (a Câmara or sector list, a census locality list, a published map). Residents can also correct their own code in the N-Ways app. |
| Correct a fact, a figure or a citation in the paper or the notes | open an issue or a pull request against `docs/`, with the source |
| Fix a bug in the engine, the server or a tool | open a pull request with a test that fails before the fix and passes after it |
| Propose a change to the code format, the check digit, the sector table or the numbering | open an issue marked *proposal*: it is published for comment for at least 30 days before a decision (GOVERNANCE.md) |
| Report a security problem | do not open an issue; see [SECURITY.md](SECURITY.md) |

Write in English, Portuguese or French.

## The registry is not edited by hand

The files in `registry/` are exports of the issuer's database, checked by `MANIFEST.json`. A pull request never edits them. Codes are issued, confirmed, moved or retired by the issuer (GOVERNANCE.md, "One issuer"), and the next export carries the change. A code is never reused and an issued number never changes.

## Before a pull request

Everything runs with Python 3.9 or later and its standard library:

```sh
python3 engine/reference/gw_codes.py          # the conformance vectors
python3 engine/reference/test_gw.py           # engine unit tests
python3 -m unittest server.tests.test_server  # registry server tests
```

All three must pass. A change to the engine must keep `engine/reference/vectors.json` unchanged (run `python3 tools/vectors.py` and check that `git diff` shows nothing), unless the change is an approved proposal, in which case the new vectors are part of it. A change to the server keeps the import and export round trip byte-identical and the issuing parity tests green.

Keep the code to the standard library, keep comments to what a reader needs to understand the rule and why it holds, and keep documents in plain, finished prose.

## Licences

By contributing you agree that your contribution is licensed as the part of the repository it belongs to: code under Apache 2.0, data under ODbL 1.0, documents under CC BY 4.0 ([LICENSING.md](LICENSING.md)).
