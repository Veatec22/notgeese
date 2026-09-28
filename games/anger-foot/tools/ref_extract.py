"""Dump the Anger Foot table with speaker, addressee and other languages -> work/ref-all.json.

Input for tools/review.py and bible evidence. Publisher content: never committed.

    .venv\\Scripts\\python.exe games\\anger-foot\\tools\\ref_extract.py "C:\\Games\\Anger Foot\\Anger Foot_Data\\resources.assets"
"""
import json
import struct
import sys
from pathlib import Path

import UnityPy

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
LANGS = {76: 'pt', 77: 'fr', 78: 'de', 79: 'slot', 80: 'ja', 81: 'ko', 82: 'es419', 83: 'ru', 84: 'zh', 85: 'es', 86: 'zht', 87: 'tr'}


def rd(b, p):
    n = struct.unpack_from('<i', b, p)[0]
    return b[p + 4:p + 4 + n].decode('utf-8'), (p + 4 + n + 3) & ~3


def main():
    out = {}
    for o in UnityPy.load(sys.argv[1]).objects:
        if o.type.name != 'MonoBehaviour':
            continue
        b = o.get_raw_data()
        try:
            p = 28
            key, p = rd(b, p); eng, p = rd(b, p); desc, p = rd(b, p); p += 8
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
        out[o.path_id] = dict(key=key, path=path, speaker=spk, to=to, note=desc, en=eng,
                              ru=tr[83], fr=tr[77], de=tr[78], es=tr[85])
    target = ROOT / 'work' / 'ref-all.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out), target)


if __name__ == '__main__':
    main()
