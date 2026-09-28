"""Integration checks against extracted, checksum-pinned SPRAWL assets."""
import struct
import tempfile
import unittest
from pathlib import Path

from asset import Asset
from game_pak import Reader, GamePak
import selector
import pak

ROOT = Path(__file__).resolve().parents[1]


def rows(body):
    r = Reader(body)
    r.at = 45
    result = {}
    for _ in range(r.get('I')):
        start = r.at
        code = r.string()
        # FriendlyName tagged FText, then FlagTexture tagged object, then None.
        r.at += 16
        size = r.get('I')
        r.at += 5 + size
        r.at += 16
        assert r.get('I') == 4
        r.at += 5
        flag = r.get('i')
        r.at += 8
        result[code] = (flag, body[start:r.at])
    assert body[r.at:r.at+8] == struct.pack('<Q', 31)
    return result


class SelectorTests(unittest.TestCase):
    def test_new_locale_preserves_all_original_rows_and_imports(self):
        source = Asset(ROOT/'work/assets'/f'{selector.LOCALE}.uasset')
        old = rows(source.b)
        self.assertEqual(len(old), 11)
        with tempfile.TemporaryDirectory() as out:
            files = selector.build_assets(ROOT/'work/assets', out)
            built = Asset(Path(out)/f'{selector.LOCALE}.uasset')
            new = rows(built.b)
            self.assertEqual(set(new), set(old) | {'pl'})
            for key, value in old.items():
                self.assertEqual(new[key], value)
            self.assertEqual(new['pl'][0], -27)
            self.assertIn(b'Polski', new['pl'][1])
            self.assertEqual(built.imports[:25], source.imports)
            archive = pak.write(files)
            path = Path(out)/'test.pak'
            path.write_bytes(archive)
            independent = GamePak(path)
            self.assertEqual(set(independent.files), set(files))
            for name, data in files.items():
                self.assertEqual(independent.extract(name), data)

    def test_flag_keeps_alpha_and_has_correct_colours(self):
        source = Asset(ROOT/'work/assets'/f'{selector.FLAG_SOURCE}.uasset')
        _, body = selector.flag_texture(source)
        pixels = body[326:326+57600]
        self.assertEqual(pixels[3::4], source.b[329:326+57600:4])
        self.assertEqual(pixels[:3], bytes((255,255,255)))
        self.assertEqual(pixels[60*120*4:60*120*4+3], bytes((60,20,220)))


if __name__ == '__main__':
    unittest.main()
