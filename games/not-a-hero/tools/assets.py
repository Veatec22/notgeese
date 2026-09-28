"""NOT A HERO GOG: indexed zlib RGBA images in Chowdren Assets.dat.

Format reference: https://github.com/snickerbockers/fp-assets (public domain).
This implementation preserves the complete original container and appends changed
images, updating only their index entries. No redistribution of the container.
"""
import struct
import zlib

from PIL import Image

TABLE = 0x92D2
IMAGE_COUNT = 18793
RECORD_COUNT = 18831


class Assets:
    def __init__(self, data: bytes):
        self.data = data
        self.offsets = struct.unpack_from(f'<{RECORD_COUNT}I', data, TABLE)

    def image(self, index: int) -> Image.Image:
        assert 0 <= index < IMAGE_COUNT
        offset = self.offsets[index]
        w, h, *_, length = struct.unpack_from('<6HI', self.data, offset)
        raw = zlib.decompress(self.data[offset + 16:offset + 16 + length])
        assert len(raw) == w * h * 4
        return Image.frombytes('RGBA', (w, h), raw)

    def build(self, images: dict[int, Image.Image]) -> bytes:
        result = bytearray(self.data)
        for index, image in sorted(images.items()):
            original = self.image(index)
            assert original.size == image.size, (index, original.size, image.size)
            offset = self.offsets[index]
            compressed = zlib.compress(image.tobytes(), 9)
            struct.pack_into('<I', result, TABLE + index * 4, len(result))
            result.extend(self.data[offset:offset + 12])
            result.extend(struct.pack('<I', len(compressed)))
            result.extend(compressed)
        # Prove that every original byte except the selected index cells survives.
        restored = bytearray(result[:len(self.data)])
        for index in images:
            at = TABLE + index * 4
            restored[at:at + 4] = self.data[at:at + 4]
        assert bytes(restored) == self.data
        check = Assets(bytes(result))
        for index, image in images.items():
            assert check.image(index).tobytes() == image.tobytes()
        return bytes(result)
