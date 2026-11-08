#!/usr/bin/env python3
"""Offline regression tests. Every test owns an isolated toolchain checkout."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TEST_BASH = os.environ.get('PALMDEV_TEST_BASH', 'bash')
LICENSE = 'Fixture license agreement for automated tests only. No real SDK is included.\n' * 2


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IsolatedTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='palmdev-tests-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'checkout with spaces'
        self.root.mkdir()
        for name in ('scripts', 'config', 'examples', 'templates'):
            shutil.copytree(ROOT / name, self.root / name, ignore=shutil.ignore_patterns('build', '__pycache__'))
        for name in ('Dockerfile', 'palm-build', 'setup.sh'):
            shutil.copy2(ROOT / name, self.root / name)
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'])
        for name in list(self.env):
            if name.startswith('PALMDEV_'):
                del self.env[name]
        self.env['TMPDIR'] = str(self.base / 'staging')
        Path(self.env['TMPDIR']).mkdir()

    def script(self, relative, *, data='', env=None, args=()):
        return subprocess.run([TEST_BASH, str(self.root / relative), *args], input=data, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.root,
                              env={**self.env, **(env or {})}, timeout=30)

    def executable(self, name, text):
        path = self.bin / name
        path.write_text(text)
        path.chmod(0o755)
        return path


class InstallerTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        self.source = self.base / 'source'
        self.source.mkdir()
        for version in ('3.1', '3.5', '4', '9.1', '9.2'):
            path = self.source / ('sdk-' + version)
            path.mkdir()
            (path / 'header.h').write_text('fixture ' + version)
            if version != '9.2':
                (path / 'License.txt').write_text(LICENSE)
        self.git('init', '-q')
        self.revision = self.commit()
        self.env.update(PALMDEV_SDK_REPO=str(self.source), PALMDEV_SDK_REV=self.revision)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), *args], text=True).strip()

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD')

    def install(self, selection='', data='', **env):
        return self.script('scripts/install-palm-sdks.sh', data=data,
                           env=dict(PALMDEV_SDK_SELECTION=selection, **env))

    def sdk(self, version):
        return self.root / '.local/sdk' / ('sdk-' + version)

    def test_fresh_default_multiple_and_repeat(self):
        p = self.install(data='agree\nagree\n')
        self.assertEqual(p.returncode, 0, p.stderr)
        for version in ('3.1', '3.5'):
            self.assertTrue((self.sdk(version) / 'header.h').exists())
        meta = self.root / '.local/licenses/sdk-3.1.accepted'
        before = meta.read_bytes()
        p = self.install()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn('Type agree', p.stdout)
        self.assertEqual(before, meta.read_bytes())
        self.assertEqual(list(Path(self.env['TMPDIR']).iterdir()), [])

    def test_single_and_incremental(self):
        self.assertEqual(self.install('3.5', 'agree\n').returncode, 0)
        (self.sdk('3.5') / 'sentinel').write_text('retain')
        p = self.install('3.5 4', 'agree\n')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.count('Type agree'), 1)
        self.assertTrue((self.sdk('3.5') / 'sentinel').exists())
        self.assertTrue(self.sdk('4').exists())

    def test_reject_and_global_acceptance_variable_ignored(self):
        p = self.install('9.1', 'decline\n', PALMDEV_LICENSE_RESPONSE='agree')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse(self.sdk('9.1').exists())
        self.assertFalse((self.root / '.local/licenses/sdk-9.1.accepted').exists())
        self.assertEqual(list(Path(self.env['TMPDIR']).iterdir()), [])

    def test_missing_and_malformed_licenses(self):
        (self.source / 'sdk-9.1/License.txt').write_bytes(b'\0invalid')
        self.env['PALMDEV_SDK_REV'] = self.commit()
        p = self.install('9.1 9.2', 'agree\nagree\n')
        self.assertIn('malformed', p.stderr)
        self.assertIn('no applicable', p.stderr)
        self.assertFalse(self.sdk('9.1').exists())
        self.assertFalse(self.sdk('9.2').exists())

    def test_unknown_version(self):
        self.assertNotEqual(self.install('unknown').returncode, 0)

    def test_legacy_hash_migration(self):
        self.install('3.5', 'agree\n')
        meta = self.root / '.local/licenses/sdk-3.5.accepted'
        meta.write_text('source_revision=' + self.revision + '\nlicense_sha256=' + 'a' * 64 + '\naccepted_at=original\n')
        p = self.install('3.5')
        self.assertNotIn('Type agree', p.stdout)
        self.assertIn('hash_version=2', meta.read_text())
        self.assertIn('accepted_at=original', meta.read_text())

    def test_changed_revision_requires_acceptance_and_decline_preserves_old(self):
        self.install('3.5', 'agree\n')
        meta = self.root / '.local/licenses/sdk-3.5.accepted'
        before = meta.read_bytes()
        (self.source / 'sdk-3.5/License.txt').write_text(LICENSE + 'Changed agreement.\n')
        self.env['PALMDEV_SDK_REV'] = self.commit()
        p = self.install('3.5', 'decline\n')
        self.assertIn('Type agree', p.stdout)
        self.assertEqual(meta.read_bytes(), before)
        self.assertEqual((self.sdk('3.5') / 'License.txt').read_text(), LICENSE)

    def test_failed_and_interrupted_download_cleanup(self):
        self.executable('git', '#!/bin/sh\nexit 23\n')
        self.assertEqual(self.install('3.5').returncode, 23)
        self.assertEqual(list(Path(self.env['TMPDIR']).iterdir()), [])
        self.executable('git', '#!/bin/sh\nkill -TERM "$PPID"\nexit 143\n')
        self.assertEqual(self.install('3.5').returncode, 143)
        self.assertEqual(list(Path(self.env['TMPDIR']).iterdir()), [])

    def test_install_rollback_and_interrupt(self):
        self.install('3.5', 'agree\n')
        module = load_module('sdk_state', self.root / 'scripts/sdk-state.py')
        dest = self.sdk('3.5')
        meta = self.root / '.local/licenses/sdk-3.5.accepted'
        before = meta.read_bytes()
        for failure in (OSError('disk full'), KeyboardInterrupt()):
            with mock.patch.object(module, 'response', return_value='agree'), mock.patch.object(module, 'write_record', side_effect=failure), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(type(failure)):
                    module.install(self.source / 'sdk-3.5', dest, meta, 'new-revision', 'fixture')
            self.assertEqual(meta.read_bytes(), before)
            self.assertEqual((dest / 'header.h').read_text(), 'fixture 3.5')
            self.assertFalse(list(dest.parent.glob('.*.stage-*')))

    def test_handspring_accept_then_skip_prompt(self):
        config = self.root / 'config/source-versions.conf'
        with config.open('a') as out:
            out.write('\nHANDSPRING_SDK_REPO=' + str(self.source) + '\nHANDSPRING_SDK_REV=' + self.revision + '\n')
        # This fixture has several applicable agreements, all must be displayed.
        p = self.script('scripts/install-handspring-sdk.sh', data='agree\n', env={'PALMDEV_HANDSPRING': 'y'})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.count('### '), 4)
        self.assertFalse((self.root / '.local/sdk/handspring/.git').exists())
        p = self.script('scripts/install-handspring-sdk.sh')
        self.assertIn('already installed', p.stdout)
        self.assertNotIn('Type agree', p.stdout)

    def test_selector_space_enter_and_existing_status(self):
        # Give the pager a nonblocking fixture implementation.
        self.executable('less', '#!/bin/sh\ncat "$3"\n')
        master, slave = pty.openpty()
        p = subprocess.Popen([TEST_BASH, str(self.root / 'scripts/install-palm-sdks.sh')], stdin=slave,
                             stdout=slave, stderr=slave, env=self.env, cwd=self.root)
        os.close(slave)
        output = b''

        def until(text):
            nonlocal output
            end = time.monotonic() + 15
            while text not in output and time.monotonic() < end:
                if select.select([master], [], [], .1)[0]:
                    try:
                        output += os.read(master, 65536)
                    except OSError:
                        break
            self.assertIn(text, output)
            output = b''

        try:
            until(b'Selection:')
            os.write(master, b' ')
            until(b'> [ ] 3.1')
            os.write(master, b'\n')
            until(b'Type agree')
            os.write(master, b'agree\n')
            self.assertEqual(p.wait(timeout=10), 0)
            self.assertFalse(self.sdk('3.1').exists())
            self.assertTrue(self.sdk('3.5').exists())
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()
            os.close(master)
        # Existing SDKs are labelled, start unselected, and allow Enter without
        # forcing another SDK to be installed or accepted.
        master, slave = pty.openpty()
        p = subprocess.Popen([TEST_BASH, str(self.root / 'scripts/install-palm-sdks.sh')], stdin=slave,
                             stdout=slave, stderr=slave, env=self.env, cwd=self.root)
        os.close(slave)
        output = b''
        try:
            until(b'3.5   installed')
            os.write(master, b' ')
            until(b'> [ ] 3.1')
            os.write(master, b'\n')
            self.assertEqual(p.wait(timeout=10), 0)
            self.assertFalse(self.sdk('3.1').exists())
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()
            os.close(master)


FAKE_DOCKER = r'''#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys
args = sys.argv[1:]
with open(os.environ['FAKE_DOCKER_LOG'], 'a') as f:
    f.write(json.dumps(args) + '\n')
if args[0] == 'info': sys.exit(int(os.environ.get('FAKE_DAEMON_FAIL', '0')))
if args[0] == '--version': print('Docker fixture'); sys.exit()
if args[:2] == ['image', 'inspect']:
    print(os.environ.get('FAKE_IMAGE_KEY', 'absent')); sys.exit()
if args[0] == 'build': sys.exit(int(os.environ.get('FAKE_BUILD_FAIL', '0')))
mounts = {}; env = os.environ.copy(); workdir = '/workspace'; entry = None; i = 1
while i < len(args):
    arg = args[i]
    if arg in ('--rm', '-it'): i += 1; continue
    if arg in ('--platform', '--user', '--entrypoint', '-w', '-v', '-e'):
        value = args[i+1]
        if arg == '-v':
            host, dest, *_ = value.split(':'); mounts[dest] = host
        if arg == '-e':
            k, v = value.split('=', 1); env[k] = v
        if arg == '-w': workdir = value
        if arg == '--entrypoint': entry = value
        i += 2; continue
    image = arg; command = args[i+1:]; break
if '/config' in mounts:
    if os.environ.get('FAKE_SPECS_FAIL'): sys.exit(12)
    pathlib.Path(mounts['/config'], 'specs').write_text('fixture specs')
    sys.exit()
if command == ['/bin/bash']: sys.exit()
cwd = mounts['/workspace'] + workdir[len('/workspace'):]
sys.exit(subprocess.call(command, cwd=cwd, env=env))
'''


class WrapperTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        (self.root / '.local/sdk/sdk-3.5').mkdir(parents=True)
        self.project = self.base / 'project with spaces'
        self.project.mkdir()
        self.log = self.base / 'docker.jsonl'
        self.env.update(PALMDEV_BACKEND='docker', FAKE_DOCKER_LOG=str(self.log))
        self.executable('docker', FAKE_DOCKER)

    def build(self, command, **kwargs):
        args = ['--sdk', '3.5', '--project', str(self.project), '--', *command]
        return self.script('palm-build', args=args, **kwargs)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_argv_and_handspring(self):
        (self.root / '.local/sdk/handspring/Include').mkdir(parents=True)
        expected = ['space value', 'first\nsecond', '', "'quoted'", '$HOME', '`literal`', '\\']
        p = self.build([sys.executable, '-c', 'import json,sys; print(json.dumps(sys.argv[1:]))', *expected])
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout), expected)
        self.assertIn('HANDSPRING_INCLUDE=/toolchain/.local/sdk/handspring/Include', self.calls()[-1])
        self.assertFalse(list((self.root / '.local/config').glob('specs-*')))

    def test_failed_command_and_specs(self):
        p = self.build([sys.executable, '-c', 'raise SystemExit(7)'])
        self.assertEqual(p.returncode, 7, p.stderr)
        self.assertEqual(self.build(['true'], env={'FAKE_SPECS_FAIL': '1'}).returncode, 12)
        self.assertFalse(list((self.root / '.local/config').glob('specs-*')))

    def test_git_root_and_workspace(self):
        subprocess.run(['git', '-C', str(self.project), 'init', '-q'], check=True)
        nested = self.project / 'apps/my app'
        nested.mkdir(parents=True)
        p = self.script('palm-build', args=['--sdk', '3.5', '--project', str(nested), '--', 'pwd'])
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), str(nested))
        self.assertIn('/workspace/apps/my app', self.calls()[-1])
        p = self.script('palm-build', args=['--sdk', '3.5', '--workspace', str(self.base), '--project', str(nested), '--', 'pwd'])
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('/workspace/project with spaces/apps/my app', self.calls()[-1])

    def test_invalid_arguments(self):
        for args in (['--sdk'], ['--sdk', 'none', '--project', str(self.project), '--', 'true'],
                     ['--sdk', '3.5', '--project', '/nonexistent', '--', 'true'],
                     ['--sdk', '3.5', '--project', str(self.project), '--workspace', str(self.bin), '--', 'true'],
                     ['--sdk', '3.5', '--project', str(self.project), '--shell']):
            self.assertNotEqual(self.script('palm-build', args=args).returncode, 0)

    def test_missing_docker(self):
        minimal = self.base / 'minimal-path'
        minimal.mkdir()
        for name in ('bash', 'dirname'):
            (minimal / name).symlink_to(shutil.which(name))
        p = self.build(['true'], env={'PATH': str(minimal)})
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('Docker is unavailable', p.stderr)

    def test_backend_selection(self):
        for os_name, arch in (('Darwin', 'arm64'), ('Darwin', 'x86_64'), ('Linux', 'x86_64'), ('Linux', 'aarch64')):
            self.executable('uname', '#!/bin/sh\ncase "$1" in -s) echo ' + os_name + ';; *) echo ' + arch + ';; esac\n')
            p = self.script('scripts/install-toolchain.sh')
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn('--platform', self.calls()[-1])
        self.assertNotEqual(self.script('scripts/install-toolchain.sh', args=['native-macos']).returncode, 0)

    def test_image_cache_uses_version_lock(self):
        key = subprocess.check_output([TEST_BASH, '-c', '. scripts/common.sh; toolchain_key'], cwd=self.root, text=True).strip()
        self.assertEqual(self.script('scripts/install-toolchain.sh', env={'FAKE_IMAGE_KEY': key}).returncode, 0)
        self.assertFalse(any(c[0] == 'build' for c in self.calls()))
        with (self.root / 'config/source-versions.conf').open('a') as out:
            out.write('\nPRC_TOOLS_REV=' + '1' * 40 + '\n')
        self.assertEqual(self.script('scripts/install-toolchain.sh', env={'FAKE_IMAGE_KEY': key}).returncode, 0)
        self.assertTrue(any(c[0] == 'build' for c in self.calls()))
        self.assertNotEqual(self.script('scripts/install-toolchain.sh', env={'FAKE_BUILD_FAIL': '9'}).returncode, 0)
        self.assertNotEqual(self.script('scripts/install-toolchain.sh', env={'FAKE_DAEMON_FAIL': '1'}).returncode, 0)


class PrcTests(unittest.TestCase):
    def test_metadata_and_resource_validation(self):
        module = load_module('check_prc', ROOT / 'scripts/check-prc.py')
        header = bytearray(78)
        header[:10] = b'HelloWorld'
        struct.pack_into('>H', header, 32, 1)
        header[60:68] = b'applHWr1'
        struct.pack_into('>H', header, 76, 4)
        table = b''.join(struct.pack('>4sHI', kind, number, 118 + i) for i, (kind, number) in enumerate(
            ((b'code', 0), (b'code', 1), (b'data', 0), (b'tFRM', 1000))))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fixture.prc'
            path.write_bytes(header + table + b'1234')
            with contextlib.redirect_stdout(io.StringIO()):
                module.check(path, 'HelloWorld', 'HWr1')
            for broken in (b'junk', bytes(header + table), bytes(header[:60] + b'BAD!' + header[64:] + table + b'1234')):
                path.write_bytes(broken)
                with self.assertRaises(ValueError):
                    module.check(path, 'HelloWorld', 'HWr1')


class ApplicationTests(IsolatedTest):
    def test_form_lifecycle_and_event_dispatch(self):
        # Host stubs check event ordering; they are not a Palm OS emulator.
        header = r'''
#ifndef TEST_PALMOS_H
#define TEST_PALMOS_H
typedef unsigned char Boolean;
typedef unsigned short UInt16;
typedef unsigned short Word;
typedef unsigned long UInt32;
typedef unsigned long DWord;
typedef char *Ptr;
typedef struct { int id; } FormType;
typedef struct { int eType; union { struct { UInt16 formID; } frmLoad; } data; } EventType;
enum { false=0, true=1, frmLoadEvent=1, frmOpenEvent=2, appStopEvent=3,
       sysAppLaunchCmdNormalLaunch=0, evtWaitForever=-1 };
FormType *FrmInitForm(UInt16);
void FrmSetActiveForm(FormType *);
FormType *FrmGetActiveForm(void);
void FrmDrawForm(FormType *);
void WinDrawChars(const char *, int, int, int);
void FrmGotoForm(UInt16);
void EvtGetEvent(EventType *, int);
Boolean SysHandleEvent(EventType *);
Boolean MenuHandleEvent(void *, EventType *, UInt16 *);
void FrmDispatchEvent(EventType *);
void FrmCloseAllForms(void);
#endif
'''
        harness = r'''
#include "PalmOS.h"
#include <assert.h>
#include <string.h>
static FormType form;
static FormType *active;
static int next, drawn, dispatched, closed;
FormType *FrmInitForm(UInt16 id) { assert(id==1000); form.id=id; return &form; }
void FrmSetActiveForm(FormType *f) { assert(f==&form); active=f; }
FormType *FrmGetActiveForm(void) { assert(active); return active; }
void FrmDrawForm(FormType *f) { assert(f==active && active); }
void WinDrawChars(const char *s,int len,int x,int y) {
    (void)x; (void)y; assert(active && len==13 && !strncmp(s,"Hello, World!",13)); drawn++;
}
void FrmGotoForm(UInt16 id) { assert(id==1000); }
void EvtGetEvent(EventType *e,int timeout) {
    static const int events[]={frmLoadEvent,frmOpenEvent,99,appStopEvent};
    (void)timeout; assert(next<4); e->eType=events[next++]; e->data.frmLoad.formID=1000;
}
Boolean SysHandleEvent(EventType *e) { (void)e; return false; }
Boolean MenuHandleEvent(void *m,EventType *e,UInt16 *err) { (void)m; (void)e; assert(err); *err=0; return false; }
void FrmDispatchEvent(EventType *e) { assert(e->eType==99 || e->eType==appStopEvent); dispatched++; }
void FrmCloseAllForms(void) { assert(active); active=0; closed++; }
#ifdef PALMDEV_LEGACY_SDK
DWord PilotMain(Word,Ptr,Word);
#else
UInt32 PilotMain(UInt16,void *,UInt16);
#endif
int main(void) {
    assert(PilotMain(0,0,0)==0);
    assert(drawn==1 && dispatched==2 && closed==1);
    return 0;
}
'''
        folder = self.base / 'harness'
        folder.mkdir()
        (folder / 'PalmOS.h').write_text(header)
        (folder / 'Pilot.h').write_text('#include "PalmOS.h"\n')
        (folder / 'harness.c').write_text(harness)
        for legacy in (False, True):
            command = ['cc', '-Wall', '-Wextra', '-Werror', '-I' + str(folder),
                       str(self.root / 'examples/hello-world/src/HelloWorld.c'),
                       str(folder / 'harness.c'), '-o', str(folder / 'test-app')]
            if legacy:
                command.append('-DPALMDEV_LEGACY_SDK')
            subprocess.run(command, check=True, capture_output=True)
            subprocess.run([str(folder / 'test-app')], check=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
