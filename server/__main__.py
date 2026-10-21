"""Command line: import, serve, export. Settings come from flags or the environment."""
import argparse
import os
import sys

from . import issue as issuing
from .store import RegistryError, Store, export_registry, import_registry

DEFAULT_DB = os.environ.get('ADDRESSES_DB', 'data/addresses.sqlite')


def main(argv=None):
    p = argparse.ArgumentParser(prog='python3 -m server', description='N-Ways Addressing for Guinea-Bissau: registry server')
    sub = p.add_subparsers(dest='cmd', required=True)
    im = sub.add_parser('import', help='load the published registry into a database')
    im.add_argument('--registry', default='registry', help='folder with MANIFEST.json and the *.csv.gz files')
    im.add_argument('--db', default=DEFAULT_DB)
    im.add_argument('--force', action='store_true', help='replace a database that holds codes issued since its import')
    sv = sub.add_parser('serve', help='serve the JSON API')
    sv.add_argument('--db', default=DEFAULT_DB)
    sv.add_argument('--host', default=os.environ.get('HOST', '0.0.0.0'))
    sv.add_argument('--port', type=int, default=int(os.environ.get('PORT', '8080')))
    ex = sub.add_parser('export', help='write the registry in the published format')
    ex.add_argument('--db', default=DEFAULT_DB)
    ex.add_argument('--out', required=True)
    a = p.parse_args(argv)
    try:
        if a.cmd == 'import':
            d = os.path.dirname(os.path.abspath(a.db))
            os.makedirs(d, exist_ok=True)
            n = import_registry(a.registry, a.db, force=a.force, log=lambda m: print(m, file=sys.stderr))
            print(f'imported {n} codes into {a.db}', file=sys.stderr)
        elif a.cmd == 'serve':
            from .api import serve
            keys = [k.strip() for k in os.environ.get('ISSUE_KEYS', '').split(',') if k.strip()]
            per_day = int(os.environ.get('ISSUE_PER_DAY', str(issuing.PER_DAY)))
            cors = os.environ.get('CORS_ORIGINS', '').split(',')
            serve(Store(a.db), a.host, a.port, keys, per_day, cors)
        elif a.cmd == 'export':
            n = export_registry(a.db, a.out)
            print(f'exported {n} codes to {a.out}', file=sys.stderr)
    except RegistryError as e:
        print(f'error: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
