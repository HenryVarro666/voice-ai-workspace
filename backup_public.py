#!/usr/bin/env python3
"""Review source-only public backups. Default: preview; push always requires confirmation.

Requires Python3.11+, Git, Gitleaks and macOS/Linux. Candidate commits live only
inside .public-backup/plans; original source branches/indexes are never changed.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import quote, unquote, urlsplit
import uuid


class BackupError(RuntimeError):
    """Failed review/safety check; never print credential values."""


DENY_SUFFIXES = set('''.wav .wave .mp3 .mp4 .flac .m4a .aac .ogg .opus .pcm .raw
.webm .mov .mkv .avi .aiff .aif .wma .safetensors .pt .pth .ckpt .bin .gguf
.onnx .npy .npz .parquet .arrow .pkl .pickle .zip .tar .gz .whl .pyc .sqlite
.db .pdf .log .pem .key .p12 .pfx'''.split())
DENY_PARTS = set('''.git .ssh .aws .public-backup node_modules __pycache__ .pytest_cache
.ruff_cache .mypy_cache .cache .claude .code-review-graph .ipynb_checkpoints
models checkpoints vendor outputs runs logs recordings private credentials secrets dist build lib'''.split())
DENY_NAMES = set('''.env .netrc .npmrc .pypirc .ds_store credentials.json secrets.json
token.json bridge-config.json auth.json service-account.json application_default_credentials.json
id_rsa id_dsa id_ed25519 authorized_keys known_hosts'''.split())
TEXT_SUFFIXES = set('''.py .ts .tsx .js .jsx .mjs .cjs .css .html .json .jsonl .csv
.toml .txt .md .svg .yml .yaml .sh .cmd .bat .ps1 .patch .cff .in .sha256'''.split())
TEXT_NAMES = {'LICENSE', 'NOTICE', 'Makefile', '.gitignore', '.gitattributes', '.editorconfig', '.gitkeep'}
MANAGED = {'PUBLICATION_MANIFEST.json', 'PUBLICATION_AUDIT.json'}
TOKENS = {
    'literal-github-token': r'gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{40,}',
    'literal-huggingface-token': r'hf_[A-Za-z0-9]{25,}',
    'literal-openai-token': r'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{25,}',
    'literal-aws-key': r'AKIA[0-9A-Z]{16}',
    'literal-private-key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'literal-url-credential': r'https?://[^\s/@:]+:[^\s/@]{6,}@',
}
EMBEDDED = re.compile(r'data:(?:audio|video|image)/[^;\s]+;base64,[A-Za-z0-9+/]{64}')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_bytes(encode(value))
    temp.chmod(0o600)
    temp.replace(path)


def run(args, *, data=None, env=None, check=True):
    result = subprocess.run(args, input=data, capture_output=True, env=env)
    if check and result.returncode:
        raise BackupError(f'{Path(args[0]).name} failed (exit {result.returncode}); no force push attempted')
    return result


def git(root, *args, **kwargs):
    return run(['git', '--no-optional-locks', '-C', str(root), *args], **kwargs)


def relative(name):
    p = Path(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or any(ord(c) < 32 for c in name):
        raise BackupError(f'Unsafe repository-relative path: {name!r}')
    return p


def excluded(name):
    p = Path(str(name).lower())
    return (any(s in DENY_SUFFIXES for s in p.suffixes)
            or any(x in DENY_PARTS or x.startswith(('.venv', 'venv')) or x.endswith('.egg-info') for x in p.parts)
            or p.name in DENY_NAMES or p.name.startswith(('.env', 'credentials.', 'secrets.', 'token.')) or '.local.' in p.name)


def tree(root, ref='HEAD'):
    files = {}
    for row in git(root, 'ls-tree', '-r', '-z', ref).stdout.split(b'\0'):
        if row:
            attrs, name = row.split(b'\t', 1)
            mode, kind, oid = attrs.decode().split()
            name = name.decode()
            relative(name)
            if kind != 'blob' or mode not in {'100644', '100755'}:
                raise BackupError(f'Public links/submodules are unsupported: {name}')
            files[name] = {'mode': mode, 'oid': oid}
    return files


def context_hash(data, first, last):
    return sha('\n'.join(data.decode().splitlines()[first - 1:last]).encode())


class Backup:
    def __init__(self, config_path):
        self.config_path = Path(config_path).resolve()
        self.root = self.config_path.parent
        self.config = json.loads(self.config_path.read_text())
        self.state_dir = (self.root / self.config['state_dir']).resolve()
        self.state_file = self.state_dir / 'state.json'
        self.objects = self.state_dir / 'objects'
        self.allow_path = (self.root / self.config['allowlist']).resolve()
        rows = json.loads(self.allow_path.read_text()).get('findings', [])
        self.allowed = {(x['repo'], x['path'], x['rule'], x['context_sha256']) for x in rows}
        self.repos = self.config['repositories']
        if not self.repos or len({r['name'] for r in self.repos}) != len(self.repos):
            raise BackupError('Repository names must be unique')
        for repo in self.repos:
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', repo['name']):
                raise BackupError('Invalid repository name')
            for key in ['source', 'public_checkout']:
                repo[key + '_path'] = (self.root / repo[key]).resolve()
            source, public = repo['source_path'], repo['public_checkout_path']
            if public == source or public.is_relative_to(source) or self.state_dir.is_relative_to(public):
                raise BackupError('Source, publication checkout and state must be separate')
            remote = repo['remote']
            if remote.startswith('https://'):
                u = urlsplit(remote)
                if (u.netloc != 'github.com' or u.path != f"/{self.config['owner']}/{repo['name']}.git"
                        or u.query or u.fragment):
                    raise BackupError('Remote does not match the configured owner/repository')
            elif not Path(remote).is_absolute() or not Path(remote).is_dir():
                raise BackupError('Use owned GitHub HTTPS or a local bare rehearsal remote')
            if git(public, 'check-ref-format', '--branch', repo['branch'], check=False).returncode:
                raise BackupError('Invalid publication branch')

    @contextmanager
    def lock(self):
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.state_dir.chmod(0o700)
        with (self.state_dir / 'lock').open('a+') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise BackupError('Another backup is running') from error
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def policy_hash(self):
        return sha(self.config_path.read_bytes() + b'\0' + self.allow_path.read_bytes() + b'\0' + Path(__file__).read_bytes())

    def store(self, data):
        key = sha(data)
        p = self.objects / key
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            p.chmod(0o600)
        return key

    def blob(self, key):
        data = (self.objects / key).read_bytes()
        if sha(data) != key:
            raise BackupError('Baseline object changed')
        return data

    def checkout(self, repo):
        public = repo['public_checkout_path']
        if git(public, 'status', '--porcelain').stdout.strip():
            raise BackupError(f"Public checkout is dirty: {repo['name']}")
        if git(public, 'remote', 'get-url', 'origin').stdout.decode().strip().rstrip('/') != repo['remote'].rstrip('/'):
            raise BackupError(f"Unexpected public origin: {repo['name']}")
        if git(public, 'branch', '--show-current').stdout.decode().strip() != repo['branch']:
            raise BackupError(f"Unexpected public branch: {repo['name']}")
        if not repo['remote'].startswith('https://'):
            if git(repo['remote'], 'rev-parse', '--is-bare-repository').stdout.strip() != b'true':
                raise BackupError('Local rehearsal remote must be bare')
        return git(public, 'rev-parse', 'HEAD').stdout.decode().strip()

    def scope(self, repo, files):
        for name in files:
            if excluded(name):
                raise BackupError(f"Forbidden public file: {repo['name']}/{name}")
            p = Path(name)
            if p.suffix.lower() not in TEXT_SUFFIXES and p.name not in TEXT_NAMES and name not in repo.get('approved_binary_paths', []):
                raise BackupError(f"Unreviewed binary/type: {repo['name']}/{name}")

    def literal_scan(self, repo, name, data):
        if name in repo.get('approved_binary_paths', []):
            if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                raise BackupError(f'Approved diagram is not PNG: {name}')
            return
        try:
            text = data.decode()
        except UnicodeDecodeError as error:
            raise BackupError(f'Unreviewed binary: {name}') from error
        if '\0' in text or EMBEDDED.search(text):
            raise BackupError(f'Binary/embedded media blocked: {name}')
        for rule, pattern in TOKENS.items():
            for m in re.finditer(pattern, text):
                line = text[:m.start()].count('\n') + 1
                key = (repo['name'], name, rule, context_hash(data, line, line + m.group().count('\n')))
                if key not in self.allowed:
                    raise BackupError(f"Credential candidate blocked: {repo['name']}/{name}:{line} ({rule}); value not displayed")

    def collect(self, repo, published):
        source, selected, ignored = repo['source_path'], {}, set()
        overrides = repo.get('overrides', {})
        preserve = MANAGED | set(repo.get('preserve', []))

        def add(origin, target):
            origin, target = relative(origin), relative(target)
            if str(target) in preserve:
                return
            if excluded(origin) or excluded(target):
                ignored.add(str(origin))
                return
            p = source / origin
            for parent in [p, *p.parents]:
                if parent == source:
                    break
                if parent.is_symlink():
                    raise BackupError(f'source symlink blocked: {origin}')
            if not p.is_file():
                return
            if p.suffix.lower() not in TEXT_SUFFIXES and p.name not in TEXT_NAMES and str(target) not in repo.get('approved_binary_paths', []):
                ignored.add(str(origin))
                return
            if p.stat().st_size > 25 * 1024 * 1024:
                raise BackupError(f'Oversized source file: {origin}')
            data = p.read_bytes()
            self.literal_scan(repo, str(target), data)
            selected[str(target)] = {'data': data, 'origin': str(origin), 'mode': '100755' if p.stat().st_mode & 0o111 else '100644'}

        for entry in repo.get('include', []):
            p = source if entry == '.' else source / relative(entry)
            if p.is_symlink():
                raise BackupError(f'source symlink blocked: {entry}')
            if p.is_file():
                add(entry, entry)
            elif p.is_dir():
                for directory, dirs, files in os.walk(p, followlinks=False):
                    dirs[:] = [n for n in dirs if not excluded((Path(directory) / n).relative_to(source))]
                    for n in dirs:
                        if (Path(directory) / n).is_symlink():
                            raise BackupError(f'source symlink blocked: {n}')
                    for n in files:
                        path = str((Path(directory) / n).relative_to(source))
                        add(path, path)
        for name in published:
            if name not in overrides:
                add(name, name)
        for target, origin in overrides.items():
            if not (source / relative(origin)).is_file():
                raise BackupError(f'Missing public document override: {origin}')
            add(origin, target)
        return selected, len(ignored)

    @staticmethod
    def signatures(files):
        return {p: {'sha256': sha(v['data']), 'origin': v['origin'], 'mode': v['mode']} for p, v in files.items()}

    def project(self, repo, name, data, available):
        if Path(name).suffix.lower() not in {'.md', '.svg'}:
            return data
        text = data.decode()
        if name.endswith('.md'):
            def link(m):
                label, target = m.group(2), m.group(3).strip('<>')
                if target.startswith('#') or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                    return m.group()
                raw, sep, anchor = unquote(target).partition('#')
                absolute = Path(os.path.abspath(repo['source_path'] / Path(name).parent / raw))
                for other in sorted(self.repos, key=lambda r: len(str(r['source_path'])), reverse=True):
                    if not absolute.is_relative_to(other['source_path']):
                        continue
                    rel = absolute.relative_to(other['source_path']).as_posix()
                    if rel.endswith('.png') and rel[:-4] + '.svg' in available[other['name']]:
                        rel = rel[:-4] + '.svg'
                    if rel in available[other['name']] or any(x.startswith(rel.rstrip('/') + '/') for x in available[other['name']]):
                        if other['name'] == repo['name']:
                            dest = quote(os.path.relpath(rel, Path(name).parent), safe='/._-')
                        else:
                            dest = f"https://github.com/{self.config.get('owner', 'local')}/{other['name']}/blob/{other['branch']}/{quote(rel, safe='/._-')}"
                        return f"{m.group(1)}[{label}]({dest}{'#' + anchor if sep else ''})"
                return label + ' — local-only artifact: ' + chr(96) + raw + chr(96)
            text = re.sub(r'(!?)\[([^\]]*)\]\((<[^>]*>|[^)]+)\)', link, text)
        text = text.replace('Derek', 'the reviewer').replace('Propio', 'the speech project')
        text = re.sub(r'/Users/[^/\s]+/Documents/', '/path/to/projects/', text)
        text = re.sub(r'/Users/[^/\s]+/', '/path/to/user/', text)
        text = re.sub(r'(?<![\d.])(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)(?![\d.])', 'HOST_IP', text)
        return text.encode()

    def initialize(self):
        with self.lock():
            if self.state_file.exists():
                raise BackupError('Already initialized; do not silently reset the baseline')
            legacy = {}
            path = self.config.get('bootstrap_source_manifest')
            if path and (self.root / path).is_file():
                for row in json.loads((self.root / path).read_text()):
                    legacy[(row['repo'], row['path'])] = row['source_sha256']
            trees, inputs = {}, {}
            for repo in self.repos:
                self.checkout(repo)
                name = repo['name']
                trees[name] = tree(repo['public_checkout_path'])
                self.scope(repo, trees[name])
                inputs[name] = self.collect(repo, trees[name])[0]
            available = {n: sorted(set(trees[n]) | set(inputs[n])) for n in trees}
            state = {'version': 1, 'repositories': {}}
            for repo in self.repos:
                name, public, rows, pending = repo['name'], repo['public_checkout_path'], {}, 0
                for path, v in inputs[name].items():
                    if path not in trees[name]:
                        continue
                    published = git(public, 'show', 'HEAD:' + path).stdout
                    projected = self.project(repo, path, v['data'], available)
                    known = v['data'] == published or projected == published or sha(v['data']) == legacy.get((name, path))
                    rows[path] = {**self.signatures({path: v})[path], 'sha256': sha(v['data']) if known else None,
                                  'projected': self.store(projected if known else published), 'public_sha256': sha(published)}
                    pending += not known
                state['repositories'][name] = {'head': git(public, 'rev-parse', 'HEAD').stdout.decode().strip(), 'files': rows}
                print(f'{name}: {len(rows)} existing files; {pending} differences remain for preview')
            save(self.state_file, state)
            print('Initialized. No source/public branch or remote was changed.')

    def scan(self, repo, stage, folder):
        scan = folder / 'scan' / repo['name']
        scan.mkdir(parents=True)
        git(stage, 'checkout-index', '--all', '--prefix=' + str(scan) + '/')
        for p in scan.rglob('*'):
            if p.is_file():
                self.literal_scan(repo, p.relative_to(scan).as_posix(), p.read_bytes())
        report = folder / (repo['name'] + '-scan.json')
        result = run(['gitleaks', 'dir', str(scan), '--redact', '--no-banner', '--log-level', 'error',
                      '--report-format', 'json', '--report-path', str(report)], check=False)
        if result.returncode not in {0, 1} or not report.is_file():
            raise BackupError('Gitleaks could not complete; publication blocked')
        findings, blocked = [], []
        for row in json.loads(report.read_text()):
            p = Path(row['File']).relative_to(scan).as_posix()
            context = context_hash((scan / p).read_bytes(), row['StartLine'], row['EndLine'])
            item = {'repo': repo['name'], 'path': p, 'rule': row['RuleID'], 'line': row['StartLine'], 'context_sha256': context}
            findings.append(item)
            if (repo['name'], p, row['RuleID'], context) not in self.allowed:
                blocked.append(item)
        save(report, {'findings': findings, 'unreviewed': blocked})
        if blocked:
            save(self.state_dir / 'last-scan-findings.json', {'unreviewed': blocked})
            raise BackupError(f'Unreviewed credential findings ({len(blocked)}); inspect .public-backup/last-scan-findings.json')

    def check_remote_history(self, repo, stage, previous, current, folder):
        if git(stage, 'merge-base', '--is-ancestor', previous, current, check=False).returncode:
            raise BackupError('Reviewed public history was rewritten: ' + repo['name'])
        commits = git(stage, 'rev-list', previous + '..' + current).stdout.decode().splitlines()
        for commit in commits:
            files = tree(stage, commit)
            self.scope(repo, files)
            for name in files:
                self.literal_scan(repo, name, git(stage, 'show', commit + ':' + name).stdout)
        if not commits:
            return
        report = folder / (repo['name'] + '-history-scan.json')
        result = run(['gitleaks', 'git', str(stage), '--log-opts=' + previous + '..' + current,
                      '--redact', '--no-banner', '--log-level', 'error', '--report-format', 'json',
                      '--report-path', str(report)], check=False)
        if result.returncode not in {0, 1} or not report.is_file():
            raise BackupError('Gitleaks history scan could not complete')
        blocked = []
        for row in json.loads(report.read_text()):
            path = relative(row['File']).as_posix()
            data = git(stage, 'show', row['Commit'] + ':' + path).stdout
            fingerprint = context_hash(data, row['StartLine'], row['EndLine'])
            if (repo['name'], path, row['RuleID'], fingerprint) not in self.allowed:
                blocked.append({'repo': repo['name'], 'path': path, 'rule': row['RuleID'],
                                'commit': row['Commit'], 'context_sha256': fingerprint})
        save(report, {'unreviewed': blocked, 'commits_checked': len(commits)})
        if blocked:
            save(self.state_dir / 'last-scan-findings.json', {'unreviewed': blocked})
            raise BackupError('Unreviewed credentials in new remote history; publication blocked')

    def merge(self, base, current, remote, folder, label):
        if current == remote or current == base:
            return remote
        if remote == base:
            return current
        if b'\0' in base + current + remote:
            raise BackupError('Binary conflict: ' + label)
        paths = [folder / ('merge-' + n) for n in ['source', 'base', 'remote']]
        for p, data in zip(paths, [current, base, remote]):
            p.write_bytes(data)
        result = run(['git', 'merge-file', '-p', *map(str, paths)], check=False)
        for p in paths:
            p.unlink()
        if result.returncode:
            raise BackupError('source/remote conflict: ' + label + '; resolve explicitly and preview again')
        return result.stdout

    def manifest(self, stage):
        git(stage, 'add', '--all')
        rows = []
        for name in git(stage, 'ls-files', '-z').stdout.split(b'\0'):
            if name and name != b'PUBLICATION_MANIFEST.json':
                data = git(stage, 'show', ':' + name.decode()).stdout
                rows.append({'path': name.decode(), 'sha256': sha(data), 'bytes': len(data)})
        p = stage / 'PUBLICATION_MANIFEST.json'
        value = json.loads(p.read_text()) if p.exists() else {}
        if value.get('files') != rows:
            value.update(date=datetime.now(timezone.utc).date().isoformat(), scope='public source and reviewed metadata; no weights/credentials/raw media', files=rows)
            p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        git(stage, 'add', 'PUBLICATION_MANIFEST.json')

    def preview(self):
        with self.lock():
            if not self.state_file.exists():
                raise BackupError('Run init before preview')
            if not shutil.which('gitleaks'):
                raise BackupError('Install Gitleaks; no scan bypass is provided')
            state = json.loads(self.state_file.read_text())
            plan_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:6]
            folder = self.state_dir / 'plans' / plan_id
            folder.mkdir(parents=True)
            stages, bases, trees, inputs, local_heads = {}, {}, {}, {}, {}
            try:
                for repo in self.repos:
                    name, public = repo['name'], repo['public_checkout_path']
                    local_heads[name] = self.checkout(repo)
                    stage = folder / 'repositories' / name
                    run(['git', 'clone', '--quiet', '--no-local', '--no-checkout', str(public), str(stage)])
                    git(stage, 'remote', 'set-url', 'origin', repo['remote'])
                    git(stage, 'fetch', '--quiet', '--no-tags', 'origin', 'refs/heads/' + repo['branch'])
                    git(stage, 'checkout', '--quiet', '-B', repo['branch'], 'FETCH_HEAD')
                    bases[name] = git(stage, 'rev-parse', 'HEAD').stdout.decode().strip()
                    if git(stage, 'merge-base', '--is-ancestor', local_heads[name], bases[name], check=False).returncode:
                        raise BackupError('Public local/remote history diverged: ' + name)
                    self.check_remote_history(repo, stage, state['repositories'][name]['head'], bases[name], folder)
                    stages[name], trees[name] = stage, tree(stage)
                    self.scope(repo, trees[name])
                    inputs[name] = self.collect(repo, trees[name])
                available = {n: sorted(set(trees[n]) | set(inputs[n][0])) for n in trees}
                plan = {'version': 1, 'id': plan_id, 'policy_hash': self.policy_hash(), 'available': available, 'repositories': []}
                for repo in sorted(self.repos, key=lambda r: r['name'] == 'voice-ai-workspace'):
                    name, stage = repo['name'], stages[repo['name']]
                    files, ignored = inputs[name]
                    old_files = state['repositories'][name]['files']
                    source_state = {}
                    for path in sorted(set(old_files) | set(files)):
                        old, v = old_files.get(path), files.get(path)
                        result = git(stage, 'show', 'HEAD:' + path, check=False)
                        theirs = result.stdout if result.returncode == 0 else None
                        if v is None:
                            if theirs is not None and sha(theirs) != old['public_sha256']:
                                raise BackupError('Deletion/remote conflict: ' + name + '/' + path)
                            if theirs is not None:
                                (stage / path).unlink()
                            continue
                        projected = self.project(repo, path, v['data'], available)
                        signature = self.signatures({path: v})[path]
                        source_state[path] = {**signature, 'projected': self.store(projected)}
                        if old and all(old.get(k) == signature[k] for k in ['sha256', 'origin', 'mode']):
                            continue
                        if old is None:
                            if theirs is not None and theirs != projected:
                                raise BackupError('New source/public conflict: ' + name + '/' + path)
                            data = projected
                        else:
                            if theirs is None:
                                raise BackupError('source/deleted remote conflict: ' + name + '/' + path)
                            data = self.merge(self.blob(old['projected']), projected, theirs, folder, name + '/' + path)
                        target = stage / path
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(data)
                        target.chmod(0o755 if v['mode'] == '100755' else 0o644)
                    if name == 'voice-ai-workspace':
                        p = stage / 'REPOSITORIES.json'
                        value = json.loads(p.read_text()) if p.exists() else {'code_repositories': []}
                        revisions = {x['name']: x['candidate'] for x in plan['repositories']}
                        for row in value['code_repositories']:
                            if row['name'] in revisions:
                                row['commit'] = revisions[row['name']]
                        if not p.exists() or value != json.loads(p.read_text()):
                            p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
                        ignore = stage / '.gitignore'
                        current = ignore.read_text() if ignore.exists() else ''
                        if '.public-backup/' not in current.splitlines():
                            ignore.write_text(current.rstrip() + '\n\n# Private backup baselines and review plans\n.public-backup/\n')
                    self.manifest(stage)
                    self.scope(repo, [x.decode() for x in git(stage, 'ls-files', '-z').stdout.split(b'\0') if x])
                    self.scan(repo, stage, folder)
                    oid = git(stage, 'write-tree').stdout.decode().strip()
                    same = oid == git(stage, 'rev-parse', 'HEAD^{tree}').stdout.decode().strip()
                    candidate = bases[name]
                    if not same:
                        env = os.environ.copy()
                        identity = self.config.get('identity', {'name': 'Public Source Backup', 'email': 'backup@example.invalid'})
                        for kind in ['AUTHOR', 'COMMITTER']:
                            env['GIT_' + kind + '_NAME'], env['GIT_' + kind + '_EMAIL'] = identity['name'], identity['email']
                        candidate = git(stage, 'commit-tree', oid, '-p', bases[name], data=('backup: reviewed public source snapshot ' + plan_id + '\n').encode(), env=env).stdout.decode().strip()
                    git(stage, 'update-ref', 'refs/heads/backup-candidate', candidate)
                    git(stage, 'checkout', '--quiet', 'backup-candidate')
                    for path, v in source_state.items():
                        result = git(stage, 'show', candidate + ':' + path, check=False)
                        v['public_sha256'] = sha(result.stdout) if result.returncode == 0 else None
                    plan['repositories'].append({'name': name, 'base': bases[name], 'candidate': candidate, 'tree': oid, 'changed': not same,
                        'source': self.signatures(files), 'source_state': source_state, 'base_paths': sorted(trees[name]),
                        'public_head_before': local_heads[name], 'excluded_count': ignored})
                    (folder / (name + '.diff')).write_bytes(git(stage, 'diff', bases[name], candidate, '--').stdout)
                plan['plan_sha256'] = sha(encode(plan))
                save(folder / 'plan.json', plan)
                self.show(folder)
                return folder
            except Exception:
                shutil.rmtree(folder)  # Only this fresh, owned scratch plan; never a source/public checkout.
                raise

    def load_plan(self, value):
        p = Path(value)
        folder = (p if p.is_absolute() else self.state_dir / 'plans' / p).resolve()
        if folder.parent != self.state_dir / 'plans' or not folder.is_dir():
            raise BackupError('Unknown plan; run preview')
        plan = json.loads((folder / 'plan.json').read_text())
        expected = plan.pop('plan_sha256')
        if sha(encode(plan)) != expected:
            raise BackupError('Plan metadata changed; preview again')
        plan['plan_sha256'] = expected
        return folder, plan

    def show(self, value, full_diff=False):
        folder, plan = self.load_plan(value)
        lines = ['# Public backup plan ' + plan['id'], '', 'Isolated local candidates only; no source/public branch or remote changed.', '']
        for row in plan['repositories']:
            stage = folder / 'repositories' / row['name']
            lines += ['## ' + row['name'], f"{row['base'][:12]} -> {row['candidate'][:12]}; source files: {len(row['source'])}; skipped files encountered: {row['excluded_count']}", '']
            lines += [git(stage, 'diff', '--name-status', row['base'], row['candidate']).stdout.decode() or 'No public changes.',
                      git(stage, 'diff', '--stat', row['base'], row['candidate']).stdout.decode(), '']
            if full_diff:
                lines.append(git(stage, 'diff', row['base'], row['candidate'], '--').stdout.decode())
        text = '\n'.join(lines)
        (folder / 'changes.md').write_text(text)
        print(text)
        print('Review: ' + str(folder / 'changes.md'))
        print('Push after review: python3 backup_public.py push ' + plan['id'])

    def push(self, value, *, confirmation):
        with self.lock():
            folder, plan = self.load_plan(value)
            self.show(folder)
            if confirmation != 'PUSH ' + plan['id']:
                raise BackupError('Exact confirmation required; nothing pushed')
            if self.policy_hash() != plan['policy_hash']:
                raise BackupError('policy/script changed after preview; create a new plan')
            repos = {r['name']: r for r in self.repos}
            for row in plan['repositories']:
                repo = repos[row['name']]
                if self.signatures(self.collect(repo, row['base_paths'])[0]) != row['source']:
                    raise BackupError('source files changed after preview: ' + repo['name'])
                if self.checkout(repo) not in {row['public_head_before'], row['candidate']}:
                    raise BackupError('Public checkout changed after preview')
                stage = folder / 'repositories' / repo['name']
                if git(stage, 'status', '--porcelain').stdout.strip() or git(stage, 'rev-parse', row['candidate'] + '^{tree}').stdout.decode().strip() != row['tree']:
                    raise BackupError('Candidate changed after review')
                head = git(stage, 'ls-remote', 'origin', 'refs/heads/' + repo['branch']).stdout.decode().split()
                if not head or head[0] not in {row['base'], row['candidate']}:
                    raise BackupError('remote branch changed after preview: ' + repo['name'])
            state = json.loads(self.state_file.read_text())
            receipt_path = folder / 'push-receipts.json'
            receipts = json.loads(receipt_path.read_text()) if receipt_path.exists() else []
            for row in plan['repositories']:
                repo = repos[row['name']]
                stage, public = folder / 'repositories' / repo['name'], repo['public_checkout_path']
                head = git(stage, 'ls-remote', 'origin', 'refs/heads/' + repo['branch']).stdout.decode().split()[0]
                if head != row['candidate']:
                    git(stage, 'push', 'origin', row['candidate'] + ':refs/heads/' + repo['branch'])
                actual = git(stage, 'ls-remote', 'origin', 'refs/heads/' + repo['branch']).stdout.decode().split()[0]
                if actual != row['candidate']:
                    raise BackupError('Remote receipt mismatch')
                if not any(x['name'] == repo['name'] for x in receipts):
                    receipts.append({'name': repo['name'], 'commit': actual, 'verified': True})
                save(receipt_path, receipts)
                state['repositories'][repo['name']] = {'head': actual, 'files': row['source_state']}
                save(self.state_file, state)
                git(public, 'fetch', '--quiet', '--no-tags', 'origin', 'refs/heads/' + repo['branch'])
                git(public, 'merge', '--ff-only', 'FETCH_HEAD')
                print(f"Verified {repo['name']}: {actual}")
            print('Completed. Receipts: ' + str(receipt_path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('public_backup_config.json'))
    sub = parser.add_subparsers(dest='action')
    sub.add_parser('init')
    sub.add_parser('preview')
    show = sub.add_parser('show')
    show.add_argument('plan')
    show.add_argument('--diff', action='store_true')
    push = sub.add_parser('push')
    push.add_argument('plan')
    args = parser.parse_args()
    os.umask(0o077)
    try:
        backup = Backup(args.config)
        if args.action == 'init':
            backup.initialize()
        elif args.action == 'show':
            backup.show(args.plan, args.diff)
        elif args.action == 'push':
            backup.show(args.plan)
            folder, plan = backup.load_plan(args.plan)
            try:
                answer = input('Type PUSH ' + plan['id'] + ' to publish; anything else cancels: ')
            except EOFError:
                answer = ''
            backup.push(folder, confirmation=answer)
        else:
            backup.preview()
    except (BackupError, OSError, ValueError, KeyError) as error:
        print('Backup stopped: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
