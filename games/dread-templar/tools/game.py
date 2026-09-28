"""Shared reading of Dread Templar's localization data.

All text lives in one TextAsset in resources.assets: a pretty-printed JSON object
keyed by language code, then category, then entry id, then 'name' / 'text'.
The shipped file is not strict JSON - one German entry carries a trailing comma,
which the game's Newtonsoft parser accepts and Python's does not.
"""
import json
import re
import struct
from pathlib import Path
import UnityPy

TEXT_PATH_ID = 393
LANGUAGES = ['eng', 'chn', 'ger', 'fre', 'rus', 'pol', 'por', 'spa', 'cht', 'jan']
CATEGORIES = ['gametext', 'cutscene', 'menu', 'emblem', 'add01', 'add02']
TRAILING_COMMA = re.compile(r',(\s*[}\]])')


def read_string(raw, pos):
    length = struct.unpack_from('<i', raw, pos)[0]
    assert 0 <= length <= len(raw) - pos - 4, (pos, length)
    return raw[pos + 4:pos + 4 + length], pos + 4 + (length + 3 & ~3)


def write_string(data):
    return struct.pack('<i', len(data)) + data + b'\0' * (-len(data) % 4)


def text_asset(resources):
    """The TextAsset object holding the localization JSON."""
    env = UnityPy.load(str(resources))
    obj = next(o for o in env.objects if o.path_id == TEXT_PATH_ID)
    raw = obj.get_raw_data()
    name, pos = read_string(raw, 0)
    assert name == b'Text', name
    body, end = read_string(raw, pos)
    return obj, raw, pos, body.decode('utf-8'), end


def load(resources):
    """The localization JSON as a dict, with the trailing comma tolerated."""
    _, _, _, body, _ = text_asset(resources)
    data = json.loads(TRAILING_COMMA.sub(r'\1', body))
    assert list(data) == LANGUAGES, list(data)
    return data


def entries(block):
    """(category, key, entry) for every entry of one language block."""
    for category in CATEGORIES:
        for key, entry in block[category].items():
            yield category, key, entry
