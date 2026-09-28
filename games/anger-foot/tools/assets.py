"""Anger Foot text asset layout, shared by the plugin build and extraction.

The game keeps 12 non-English translations per LocalizedString, indexed by the position
of the language in a list sorted by LocalizationLanguage.SpreadsheetKey. The empty
ITALIAN slot (index 4) is the one the plugin takes over for Polish; SpreadsheetKey must
stay 'ITALIAN' or every index shifts.
"""
import struct

LANG_PATHID = 79          # the Italian LocalizationLanguage record in sharedassets0.assets
SLOT = 4                  # its position in every entry's translation array
SLOT_ORDER = ['CHINESE SIMPLIFIED', 'CHINESE TRADITIONAL', 'FRENCH', 'GERMAN', 'ITALIAN',
              'JAPANESE', 'KOREAN', 'PORTUGUESE BRAZILIAN', 'RUSSIAN', 'SPANISH',
              'SPANISH LATAM', 'TURKISH']


def rd(b, p):
    """Aligned Unity string at p -> (text, next position)."""
    n = struct.unpack_from('<i', b, p)[0]
    return b[p + 4:p + 4 + n].decode('utf-8'), (p + 4 + n + 3) & ~3


def wr(s):
    e = s.encode('utf-8')
    out = struct.pack('<i', len(e)) + e
    return out + b'\x00' * ((-len(out)) % 4)


def parse_entry(b):
    """LocalizedString raw data -> dict(key, eng, tr, path, list_start, tail), or None."""
    p = 28
    key, p = rd(b, p); eng, p = rd(b, p); desc, p = rd(b, p)
    head = p
    p += 8
    spk, p = rd(b, p); to, p = rd(b, p)
    n = struct.unpack_from('<i', b, p)[0]
    if n != 12:
        return None
    p += 4
    tr = []
    for _ in range(n):
        fid, pid = struct.unpack_from('<iq', b, p); p += 12
        v, p = rd(b, p)
        tr.append((fid, pid, v))
    guid, p = rd(b, p); path, p = rd(b, p)
    if len(b) - p != 16:
        return None
    return dict(key=key, eng=eng, tr=tr, path=path, list_start=head + 8 + len(wr(spk)) + len(wr(to)), tail=p)
