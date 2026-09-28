"""Extract Rain World's English texts into work/en.json.

Reads strings.txt of the base game and DLCs and decrypts conversations. Adds context to each
strings.txt entry: the game classes where the text sits in code (literal dump via
tools/StrMap.cs). Writes nothing outside work/.

    .venv\\Scripts\\python.exe games\\rain-world\\tools\\extract.py [--game "C:\\Games\\Rain World"]

Keys:
    str:<strings.txt key>          game key (English text or id)
    dlg:<file>#<line>              conversation line; text without engine instructions
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rw  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work'
CSC = Path(r'C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe')


def literal_map(game: Path) -> dict[str, list[str]]:
    managed = game / rw.DATA / 'Managed'
    exe = WORK / 'StrMap.exe'
    tsv = WORK / 'ldstr.tsv'
    if not exe.exists():
        cecil = managed / 'Mono.Cecil.dll'
        subprocess.run([str(CSC), '/nologo', f'/r:{cecil}', f'/out:{exe}', str(ROOT / 'tools/StrMap.cs')], check=True)
        (WORK / 'Mono.Cecil.dll').write_bytes(cecil.read_bytes())
    subprocess.run([str(exe), str(managed / 'Assembly-CSharp.dll'), str(tsv)], check=True)
    uses: dict[str, list[str]] = defaultdict(list)
    for line in tsv.read_text(encoding='utf-8').splitlines():
        where, literal = line.split('\t', 1)
        literal = literal.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t').replace('\\\\', '\\')
        owner = where.split('::')[0]
        if owner not in uses[literal]:
            uses[literal].append(owner)
    return uses


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, default=rw.DEFAULT_GAME)
    parser.add_argument('--ref', default='rus', help='game language dumped to work/ref-<lang>.json (bible evidence)')
    args = parser.parse_args()
    game = args.game.resolve()
    WORK.mkdir(exist_ok=True)

    key = rw.encryption_string(game)
    uses = literal_map(game)
    entries: dict[str, dict] = {}

    for source in rw.SOURCES:
        path = rw.streaming(game) / rw.SOURCES[source] / 'text_eng' / 'strings.txt'
        for k, english in rw.read_strings(path).items():
            entry = entries.setdefault(f'str:{k}', {'english': english, 'source': source})
            if entry['english'] != english:
                entry.setdefault('variants', {})[source] = english
            if uses.get(k):
                entry['context'] = ', '.join(uses[k])

    dialogue_count = 0
    for source in rw.SOURCES:
        for path in rw.dialogue_files(game, source):
            _, lines = rw.read_dialogue(path, key)
            for line in lines:
                entries[f'dlg:{path.name}#{line.index}'] = {'english': line.text, 'source': source}
                dialogue_count += 1

    # Another game language under the same keys: gender and meaning where English is silent.
    ref: dict[str, str] = {}
    for source in rw.SOURCES:
        path = rw.streaming(game) / rw.SOURCES[source] / f'text_{args.ref}' / 'strings.txt'
        if path.exists():
            ref.update({f'str:{k}': v for k, v in rw.read_strings(path).items()})
        for path in rw.dialogue_files(game, source, args.ref):
            try:
                _, lines = rw.read_dialogue(path, key, args.ref)
            except (KeyError, UnicodeError):
                continue
            for line in lines:
                ref[f'dlg:{path.name.lower()}#{line.index}'] = line.text
    (WORK / f'ref-{args.ref}.json').write_text(json.dumps(ref, ensure_ascii=False, indent=1), encoding='utf-8')

    (WORK / 'en.json').write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    strings = sum(1 for k in entries if k.startswith('str:'))
    words = sum(len(e['english'].replace('<LINE>', ' ').split()) for e in entries.values())
    print(json.dumps({'strings': strings, 'dialogue_lines': dialogue_count, 'words': words,
                      'with_context': sum(1 for e in entries.values() if 'context' in e)}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
