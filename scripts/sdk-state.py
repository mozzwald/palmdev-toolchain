#!/usr/bin/env python3
"""Review SDK agreements and replace local SDKs with rollback on failure."""
import argparse
import datetime
import hashlib
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile


def agreements(source):
    files = sorted(p for p in source.rglob('*') if p.is_file()
                   and '.git' not in p.relative_to(source).parts
                   and re.search(r'license|eula', p.name, re.I))
    if not files:
        raise ValueError('no applicable EULA/license found')
    for path in files:
        data = path.read_bytes()
        if b'\0' in data or len(data.strip()) < 80:
            raise ValueError('empty, malformed or binary license: ' + str(path.relative_to(source)))
        text = document_text(data)
        if not re.search(r'license|agreement|eula', text, re.I):
            raise ValueError('unrecognizable license: ' + str(path.relative_to(source)))
    return files


def document_text(data):
    for encoding in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass


def digest(source, files):
    h = hashlib.sha256()
    for path in files:
        name = path.relative_to(source).as_posix().encode()
        data = path.read_bytes()
        h.update(len(name).to_bytes(8, 'big') + name)
        h.update(len(data).to_bytes(8, 'big') + data)
    return h.hexdigest()


def metadata(path):
    try:
        return dict(line.split('=', 1) for line in path.read_text().splitlines() if '=' in line)
    except (OSError, ValueError):
        return {}


def accepted(dest, meta, revision):
    record = metadata(meta)
    if not dest.is_dir() or record.get('source_revision') != revision:
        return False
    try:
        files = agreements(dest)
        if record.get('hash_version') == '2':
            return record.get('license_sha256') == digest(dest, files)
        # Handspring's old record used the single file's content checksum.
        return len(files) == 1 and record.get('license_sha256') == hashlib.sha256(files[0].read_bytes()).hexdigest()
    except (ValueError, OSError):
        return False


def write_record(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as out:
            out.write(''.join(k + '=' + v + '\n' for k, v in record.items()))
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def response(prompt):
    # One invocation must not buffer answers intended for the next SDK's process.
    # Read one line directly, preserving the remaining stdin bytes for that process.
    print(prompt, end='', flush=True)
    line = bytearray()
    while True:
        char = os.read(sys.stdin.fileno(), 1)
        if not char or char == b'\n':
            return line.decode('utf-8', errors='replace').rstrip('\r')
        line.extend(char)


def install(source, dest, meta, revision, label):
    try:
        files = agreements(source)
        checksum = digest(source, files)
    except (ValueError, OSError) as error:
        print(label + ': ' + str(error) + '; skipped.', file=sys.stderr)
        return 4
    record = metadata(meta)
    if dest.is_dir() and record.get('source_revision') == revision:
        try:
            same_files = digest(dest, agreements(dest)) == checksum
        except (ValueError, OSError):
            same_files = False
        legacy = (record.get('hash_version') is None and bool(record.get('accepted_at'))
                  and re.fullmatch(r'[0-9a-f]{64}', record.get('license_sha256', '')))
        if same_files and (legacy or record.get('license_sha256') == checksum):
            # Migrate old Palm records whose checksum included a random staging path.
            # The installed and pinned agreements must match byte for byte.
            record.update(hash_version='2', license_sha256=checksum)
            write_record(meta, record)
            print(label + ' already installed and accepted; skipping.')
            return 0
    print('--- ' + label + ' license(s) ---', flush=True)
    for path in files:
        print('### ' + path.relative_to(source).as_posix(), flush=True)
        if sys.stdin.isatty() and sys.stdout.isatty() and shutil.which('less'):
            print('Opening license viewer — press q to quit and continue setup.', flush=True)
            subprocess.run(['less', '-P', 'Press q to quit the license viewer and continue setup.', str(path)], check=True)
        else:
            print(document_text(path.read_bytes()), flush=True)
    answer = response('Type agree to install ' + label + ': ')
    if answer != 'agree':
        print(label + ' declined; no files installed.')
        return 3

    dest.parent.mkdir(parents=True, exist_ok=True)
    # Stage and back up on the same filesystem as the destination. TemporaryDirectory
    # removes uninstalled files on exceptions and handled signals.
    with tempfile.TemporaryDirectory(prefix='.' + dest.name + '.stage-', dir=dest.parent) as temp:
        stage = Path(temp) / 'sdk'
        backup = Path(temp) / 'previous'
        shutil.copytree(source, stage, ignore=shutil.ignore_patterns('.git'))
        old_meta = meta.read_bytes() if meta.exists() else None
        # Signals are delivered after the critical directory/metadata transaction.
        # Copying and license review remain interruptible. SIGKILL cannot be handled.
        blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM, signal.SIGHUP})
        try:
            if dest.exists():
                dest.rename(backup)
            stage.rename(dest)
            write_record(meta, dict(source_revision=revision, hash_version='2', license_sha256=checksum,
                                   accepted_at=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')))
        except BaseException:
            if not stage.exists() and dest.exists():
                shutil.rmtree(dest)
            if backup.exists():
                backup.rename(dest)
            if old_meta is None:
                if meta.exists():
                    meta.unlink()
            elif not meta.exists() or meta.read_bytes() != old_meta:
                meta.write_bytes(old_meta)
            raise
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
    print('Installed ' + label + ' at ' + str(dest))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    status = sub.add_parser('status')
    for p in (status, sub.add_parser('install')):
        p.add_argument('dest', type=Path)
        p.add_argument('meta', type=Path)
        p.add_argument('revision')
    sub.choices['install'].add_argument('source', type=Path)
    sub.choices['install'].add_argument('label')
    args = parser.parse_args()
    if args.command == 'status':
        return 0 if accepted(args.dest, args.meta, args.revision) else 1
    return install(args.source, args.dest, args.meta, args.revision, args.label)


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print('SDK installation failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
