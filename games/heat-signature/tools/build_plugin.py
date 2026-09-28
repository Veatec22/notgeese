"""Build the native localization plugin; no installation and no game launch."""
import argparse
import hashlib
import json
import sys
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
import font_assets

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from translations import load_entries  # noqa: E402

import texts  # noqa: E402

VERSION = '0.1'


def compiler_environment():
    vswhere = Path(os.environ['ProgramFiles(x86)']) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    vs = subprocess.check_output([str(vswhere), '-latest', '-property', 'installationPath'], text=True).strip()
    script = Path(vs) / 'VC/Auxiliary/Build/vcvars32.bat'
    output = subprocess.check_output(f'"{script}" >nul && set', shell=True, text=True)
    return dict(line.split('=', 1) for line in output.splitlines() if '=' in line and not line.startswith('='))


def build(binary_only=False):
    out = ROOT / 'dist'
    work = ROOT / 'work/build'
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    mh = ROOT / 'work/minhook-1.3.4'
    if not (mh / 'include/MinHook.h').is_file():
        raise SystemExit('Missing MinHook 1.3.4 source in work/minhook-1.3.4; see technical.md')
    exports = ['Direct3DCreate9', 'Direct3DCreate9Ex', 'Direct3DShaderValidatorCreate9',
               'D3DPERF_BeginEvent', 'D3DPERF_EndEvent', 'D3DPERF_SetMarker',
               'D3DPERF_SetRegion', 'D3DPERF_QueryRepeatFrame', 'D3DPERF_SetOptions',
               'D3DPERF_GetStatus', 'DebugSetLevel', 'DebugSetMute', 'PSGPError', 'PSGPSampleTexture']
    proxy = ['#include <windows.h>', 'extern "C" FARPROC __cdecl Resolve(const char*);']
    for name in exports:
        proxy.extend([f'static const char name_{name}[] = "{name}";',
                      f'extern "C" __declspec(naked) void proxy_{name}() {{',
                      '  __asm { pushad }', f'  __asm {{ push offset name_{name} }}',
                      '  __asm { call Resolve }', '  __asm { add esp, 4 }',
                      '  __asm { mov dword ptr [esp+28], eax }', '  __asm { popad }',
                      '  __asm { jmp eax }', '}'])
    (work / 'Proxy.cpp').write_text('\n'.join(proxy), encoding='utf-8')
    (work / 'Proxy.def').write_text('LIBRARY d3d9\nEXPORTS\n' + '\n'.join(f'{n}=proxy_{n}' for n in exports), encoding='ascii')
    env = compiler_environment()
    compiler = shutil.which('cl.exe', path=next(v for k, v in env.items() if k.lower() == 'path'))
    if not compiler:
        raise SystemExit('MSVC x86 compiler is unavailable')
    sources = [mh / 'src' / name for name in ['buffer.c', 'hook.c', 'trampoline.c', 'hde/hde32.c']]
    subprocess.run([compiler, '/nologo', '/c', '/O2', '/MT', '/W3', '/I' + str(mh / 'include'),
                    *map(str, sources)], cwd=work, env=env, check=True)
    subprocess.run([compiler, '/nologo', '/LD', '/O2', '/MT', '/EHsc', '/std:c++17', '/utf-8', '/W4',
                    '/I' + str(mh / 'include'), str(ROOT / 'plugin/Plugin.cpp'), str(work / 'Proxy.cpp'),
                    *[str(work / (p.stem + '.obj')) for p in sources], 'version.lib', 'user32.lib',
                    '/link', '/DEF:' + str(work / 'Proxy.def'), '/OUT:' + str(out / 'd3d9.dll')],
                   cwd=work, env=env, check=True)
    if binary_only:
        print('Plugin built; binary-only technical preparation, no translation package.')
        return
    # The only translation file: en-pl-review.json; texts.py splits it into game texts
    # and item-name grammar.
    translations = texts.plain()
    items = texts.items()
    plain = [r for r in load_entries(ROOT) if not r['key'].startswith('item-')]
    assert translations
    assert all('\t' not in en + pl for en, pl in translations.items())
    dialog = {r['key'] for r in plain if r['context'].startswith('Dialog:')}
    rows = {}
    token = re.compile(r'<[A-Za-z]+>')
    for en, pl in translations.items():
        if token.fullmatch(en):
            continue  # a bare <ProblemDescription> line would match everything
        names = token.findall(en)
        if names:
            # Dialogue substitutions become template holes, in EN order.
            for i, name in enumerate(dict.fromkeys(names)):
                en, pl = en.replace(name, '{%d}' % i), pl.replace(name, '{%d}' % i)
            rows[en] = ('T', pl)
        elif re.search(r'\{\d\}', en):
            rows[en] = ('T', pl)
        else:
            rows[en] = ('D' if en in dialog else 'E', pl)
    # GameMaker callers may already have expanded # line separators. Preserve both
    # full strings and aligned individual lines without translating control markers.
    for en, (kind, pl) in list(rows.items()):
        if kind == 'T':
            continue
        rows.setdefault(en.replace('#', '\n'), (kind, pl.replace('#', '\n')))
        en_lines, pl_lines = re.split(r'[#\r\n]', en), re.split(r'[#\r\n]', pl)
        if len(en_lines) == len(pl_lines) and len(en_lines) > 1:
            for left, right in zip(en_lines, pl_lines):
                if left.strip():
                    rows.setdefault(left.strip(), ('E', right.strip()))
    def escape(value):
        return value.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r')
    lines = [f'{kind}\t{escape(en)}\t{escape(pl)}\n' for en, (kind, pl) in rows.items()]
    lines += [f'N\t{en}\t{noun}\t{gender}\n' for en, (noun, gender) in items['nouns'].items()]
    lines += [f'A\t{en}\t' + '\t'.join(forms) + '\n' for en, forms in items['modifiers'].items()]
    lines += [f'P\t{en}\t{phrase}\n' for en, phrase in items['tails'].items()]
    payload = out / 'notgeese'
    payload.mkdir(exist_ok=True)
    (payload / 'pl.tsv').write_bytes(''.join(lines).encode('utf-8'))
    (payload / 'LICENSE-MINHOOK.txt').write_bytes((mh / 'LICENSE.txt').read_bytes())
    (payload / 'LICENSE-XOLONIUM.txt').write_bytes((ROOT / 'fonts/LICENSE.txt').read_bytes())
    font_files = font_assets.build(payload / 'fonts')
    (out / 'READ-ME.txt').write_bytes((ROOT / 'docs/INSTALL.txt').read_bytes())
    files = ['d3d9.dll', 'notgeese/pl.tsv', 'notgeese/LICENSE-MINHOOK.txt', 'notgeese/LICENSE-XOLONIUM.txt', 'READ-ME.txt']
    files += ['notgeese/fonts/' + name for name in font_files]
    archive = out / f'Heat-Signature-PL-{VERSION}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in files:
            z.write(out / name, name)
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist()) == set(files)
        assert not any(n.lower().endswith(('.exe', '.win', '.ogg')) for n in z.namelist())
        assert all(not n.endswith('.png') or n in ['notgeese/fonts/' + f for f in font_files] for n in z.namelist())
        assert z.testzip() is None
    (out / 'build-report.json').write_text(json.dumps({'version': VERSION, 'entries': len(translations),
        'package_bytes': archive.stat().st_size, 'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
        'runtime_test': False, 'files': files}, indent=2) + '\n', encoding='utf-8')
    print(f'Built {archive}: {len(translations)} entries; runtime test pending')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary-only', action='store_true')
    build(p.parse_args().binary_only)
