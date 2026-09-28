"""Regression checks for the UE4 v11 footer, independently of pak.read()."""
import struct
import unittest

import pak


class PakFooterTests(unittest.TestCase):
    def test_unencrypted_archive_has_zero_key_guid(self):
        archive = pak.write({'Sprawl/Content/test.txt': b'test'})
        # UE4 v11 reads a 221-byte FPakInfo, starting with a 16-byte FGuid.
        footer = archive[-221:]
        self.assertEqual(footer[:16], bytes(16))
        self.assertEqual(footer[16], 0)
        self.assertEqual(struct.unpack_from('<II', footer, 17), (0x5A6F12E1, 11))
        offset, size = struct.unpack_from('<qq', footer, 25)
        self.assertEqual(offset + size, len(archive) - 221)


if __name__ == '__main__':
    unittest.main()
