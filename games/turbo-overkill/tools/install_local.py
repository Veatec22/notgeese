"""Repo-only test installation/restore with a receipt. Never starts the game."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def target(root, relative):
    path = (root/relative).resolve()
    assert path.is_relative_to(root) and path != root, relative
    return path

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game', type=Path, required=True)
    ap.add_argument('--restore', action='store_true')
    args = ap.parse_args()
    game = args.game.resolve()
    assert (game/'Turbo Overkill.exe').is_file(), 'Wrong game directory'
    processes = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Turbo Overkill.exe', '/FO', 'CSV', '/NH'], capture_output=True).stdout
    if b'Turbo Overkill.exe' in processes:
        raise SystemExit('Close Turbo Overkill first. The tool will not stop or launch it.')
    backup = (REPO/'backups/turbo-overkill').resolve()
    receipt = backup/'install-receipt.json'
    previous = json.loads(receipt.read_text()) if receipt.exists() else None
    if previous:
        assert previous['game'] == str(game), 'Receipt is for another installation'
    if args.restore:
        assert previous, 'No installation receipt'
        for row in previous['files']:
            dest = target(game, row['path'])
            if not dest.exists():
                continue
            assert digest(dest) == row['installed_sha256'], 'Changed since installation: '+row['path']
        for row in previous['files']:
            dest = target(game, row['path'])
            if row['original_sha256'] is not None:
                source = target(backup/'originals', row['path'])
                assert digest(source) == row['original_sha256']
                shutil.copy2(source, dest)
            elif dest.exists():
                dest.unlink()  # Exactly one validated, unchanged installed file.
        previous['restored'] = True
        receipt.write_text(json.dumps(previous, indent=2)+'\n')
        print('Restored originals and removed added package files. Empty folders/cache are retained.')
        return

    report = json.loads((ROOT/'work/build-report.json').read_text())
    archive = ROOT/'dist'/Path(report['package']).name
    assert digest(archive) == report['sha256'], 'Package differs from validated build'
    before = {str(p.relative_to(game)): (p.stat().st_size,p.stat().st_mtime_ns)
              for p in game.rglob('*') if p.is_file()}
    with zipfile.ZipFile(archive) as package:
        names = [n for n in package.namelist() if not n.endswith('/')]
        assert set(names) == set(report['files_sha256'])
        rows = []
        contents = {name: package.read(name) for name in names}
        old_rows = {r['path']: r for r in previous['files']} if previous else {}
        for name in names:
            dest = target(game, name)
            console_config = name == 'BepInEx/config/BepInEx.cfg' and dest.exists()
            if console_config:
                # User requested only hiding the console; retain all other settings.
                raw = dest.read_bytes()
                text = raw.decode('utf-8-sig')
                pattern = r'(?ms)(^\[Logging\.Console\].*?^Enabled\s*=\s*)[^\r\n]+'
                text, changed = re.subn(pattern, lambda m: m.group(1)+'false', text, count=1)
                if not changed:
                    raise SystemExit('Console setting not found; preserving existing config.')
                contents[name] = text.encode('utf-8')
                if name not in old_rows:
                    keep = target(backup/'originals', name)
                    keep.parent.mkdir(parents=True, exist_ok=True)
                    if not keep.exists(): shutil.copy2(dest, keep)
                    old_rows[name] = {'original_sha256': digest(keep)}
            if dest.exists() and name not in old_rows:
                # Preserve any existing mod/configuration; do not silently adopt it.
                raise SystemExit('Unmanaged existing file: '+str(dest))
            if dest.exists() and name in old_rows and not console_config and not previous.get('restored'):
                assert digest(dest) == old_rows[name]['installed_sha256'], 'Local file changed: '+name
            rows.append({'path': name, 'original_sha256': old_rows.get(name,{}).get('original_sha256'),
                         'installed_sha256': hashlib.sha256(contents[name]).hexdigest()})
        backup.mkdir(parents=True, exist_ok=True)
        evidence = {'game': str(game), 'package': str(archive), 'package_sha256': report['sha256'],
                    'files': rows, 'restored': False, 'installation_complete': False}
        receipt.write_text(json.dumps(evidence, indent=2)+'\n')
        for row in rows:
            dest = target(game, row['path'])
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(contents[row['path']])
            assert digest(dest) == row['installed_sha256']
    installed = set(names)
    untouched = 0
    for name, stat in before.items():
        if Path(name).as_posix() in installed:
            continue
        path = target(game, name)
        assert (path.stat().st_size,path.stat().st_mtime_ns) == stat, 'Original changed: '+name
        untouched += 1
    evidence['installation_complete'] = True
    evidence['original_files_unchanged_by_size_and_mtime'] = untouched
    receipt.write_text(json.dumps(evidence, indent=2)+'\n')
    print(json.dumps({'installed': len(rows), 'unchanged_original_files': untouched, 'receipt': str(receipt)}))

if __name__ == '__main__':
    main()
