"""Extract every LocalizedString from an original Anger Foot resources.assets into JSON."""
import json, struct, sys
from pathlib import Path
import UnityPy
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = sys.argv[1] if len(sys.argv) > 1 else 'backup/resources.assets'
LANGS = {76:'pt-BR',77:'fr',78:'de',79:'slot',80:'ja',81:'ko',82:'es-419',83:'ru',84:'zh-hans',85:'es',86:'zh-hant',87:'tr'}

def rd(b, p):
    n = struct.unpack_from('<i', b, p)[0]
    return b[p+4:p+4+n].decode('utf-8'), (p+4+n+3) & ~3

env = UnityPy.load(SRC)
rows = []
for o in env.objects:
    if o.type.name != 'MonoBehaviour':
        continue
    b = o.get_raw_data()
    try:
        p = 28
        key, p = rd(b, p); eng, p = rd(b, p); desc, p = rd(b, p)
        p += 8
        spk, p = rd(b, p); to, p = rd(b, p)
        n = struct.unpack_from('<i', b, p)[0]; p += 4
        if not 0 <= n <= 20:
            continue
        tr = {}
        for _ in range(n):
            fid, pid = struct.unpack_from('<iq', b, p); p += 12
            v, p = rd(b, p); tr[pid] = v
        guid, p = rd(b, p); path, p = rd(b, p)
        if len(b) - p != 16 or set(tr) != set(LANGS):
            continue
    except Exception:
        continue
    rows.append(dict(pathid=o.path_id, path=path, key=key, english=eng, note=desc,
                     speaker=spk, to=to, fr=tr[77], de=tr[78]))
rows.sort(key=lambda r: r['path'])
Path('source').mkdir(exist_ok=True)
Path('source/entries.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
empty = [r for r in rows if not r['english'].strip()]
words = sum(len(r['english'].split()) for r in rows)
print(f'entries {len(rows)} | empty english {len(empty)} | english words {words}')
groups = {}
for r in rows:
    g = '/'.join(r['path'].split('/')[:2])
    groups[g] = groups.get(g, 0) + 1
for g, n in sorted(groups.items(), key=lambda kv: -kv[1])[:14]:
    print(f'  {g:38} {n}')
