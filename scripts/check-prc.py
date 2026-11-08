#!/usr/bin/env python3
"""Check a sample PRC's resource table, application identity and executable resources."""
import argparse
from pathlib import Path
import struct
import sys


def check(path, name, creator):
    data = path.read_bytes()
    if len(data) < 78:
        raise ValueError('truncated database header')
    if data[:32].split(b'\0', 1)[0] != name.encode('ascii'):
        raise ValueError('incorrect application name')
    if not struct.unpack_from('>H', data, 32)[0] & 1:
        raise ValueError('not a resource database')
    if data[60:68] != b'appl' + creator.encode('ascii'):
        raise ValueError('incorrect application type or creator')
    if struct.unpack_from('>I', data, 72)[0]:
        raise ValueError('unexpected chained resource table')
    count = struct.unpack_from('>H', data, 76)[0]
    table_end = 78 + count * 10
    if not count or table_end > len(data):
        raise ValueError('missing or truncated resource table')
    resources = []
    for i in range(count):
        kind, number, offset = struct.unpack_from('>4sHI', data, 78 + i * 10)
        if offset < table_end or offset >= len(data):
            raise ValueError('resource offset outside database')
        resources.append((kind, number, offset))
    offsets = [r[2] for r in resources]
    if offsets != sorted(set(offsets)):
        raise ValueError('overlapping or unordered resource offsets')
    identities = {(r[0], r[1]) for r in resources}
    if len(identities) != count:
        raise ValueError('duplicate resource identity')
    for identity in ((b'code', 0), (b'code', 1), (b'data', 0), (b'tFRM', 1000)):
        if identity not in identities:
            raise ValueError('missing resource ' + repr(identity))
    print('{}: valid appl/{}, {} resources, {} bytes'.format(path, creator, count, len(data)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('prc', type=Path)
    p.add_argument('--name', default='HelloWorld')
    p.add_argument('--creator', default='HWr1')
    args = p.parse_args()
    try:
        check(args.prc, args.name, args.creator)
    except (OSError, ValueError, struct.error) as error:
        print(str(args.prc) + ': ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
