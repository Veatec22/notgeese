"""Read Broforce text banks (Localisation.StringLanguageBank) from resources.assets.

The Unity 2017 game ships no type trees, so MonoBehaviours are read raw:
m_GameObject, m_Enabled, m_Script, m_Name, then a list of (key, text) pairs.
The script class is recognized by its MonoScript in globalgamemanagers.assets.
"""

from __future__ import annotations

import struct
from pathlib import Path

import UnityPy

BANK_CLASS = 'StringLanguageBank'


def _string(raw: bytes, pos: int) -> tuple[str, int]:
    n = struct.unpack_from('<i', raw, pos)[0]
    s = raw[pos + 4:pos + 4 + n].decode('utf-8')
    pos += 4 + n
    return s, pos + (-pos) % 4


def _parse(raw: bytes) -> tuple[str, dict[str, str]]:
    name, pos = _string(raw, 28)
    count = struct.unpack_from('<i', raw, pos)[0]
    pos += 4
    values = {}
    for _ in range(count):
        key, pos = _string(raw, pos)
        value, pos = _string(raw, pos)
        values[key] = value
    assert pos == len(raw), f'bank {name}: {len(raw) - pos} bytes unread'
    return name, values


def read_banks(resources: Path) -> dict[str, dict[str, str]]:
    data = resources.parent
    env = UnityPy.load(str(data / 'globalgamemanagers.assets'), str(resources))
    scripts = {}
    for obj in env.objects:
        if obj.type.name == 'MonoScript':
            scripts[(obj.assets_file.name, obj.path_id)] = obj.read().m_ClassName

    banks = {}
    for obj in env.objects:
        if obj.assets_file.name != resources.name or obj.type.name != 'MonoBehaviour':
            continue
        raw = obj.get_raw_data()
        file_id, path_id = struct.unpack_from('<iq', raw, 16)
        external = resources.name if file_id == 0 else obj.assets_file.externals[file_id - 1].path.split('/')[-1]
        if scripts.get((external, path_id)) != BANK_CLASS:
            continue
        name, values = _parse(raw)
        banks[name] = values
    if 'en' not in banks:
        raise SystemExit(f'No English text bank found in {resources}.')
    return banks
