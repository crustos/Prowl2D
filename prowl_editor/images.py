"""images.py: true-colour pictures (RGBA PNG) in a project, for what a palette of 256 colours cannot draw smoothly: the layers behind and in front of a level (parallax.py)
and the smooth skin over its square tiles. A project keeps the PNG bytes as they are (base64 in the JSON); the viewport decodes them once into a linear-filtered texture.
No GUI and no engine in here, so it can be tested on its own (decoding uses Pillow if there is one, else Qt)."""
import base64
import struct
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_IMAGE_SIDE = 8192            # the renderer's GFX_MAX_SIZE


class ImageError(ValueError):
    pass


def png_size(data):
    """(width, height) from a PNG's header, or ImageError if these bytes are not a PNG."""
    if not isinstance(data, (bytes, bytearray)) or len(data) < 33 or bytes(data[:8]) != PNG_SIGNATURE or bytes(data[12:16]) != b"IHDR":
        raise ImageError("not a PNG")
    w, h = struct.unpack(">II", bytes(data[16:24]))
    if not (1 <= w <= MAX_IMAGE_SIDE and 1 <= h <= MAX_IMAGE_SIDE):
        raise ImageError("an image is between 1x1 and %dx%d pixels (got %dx%d)" % (MAX_IMAGE_SIDE, MAX_IMAGE_SIDE, w, h))
    return w, h


class Image:
    def __init__(self, name, png):
        self.name = name
        self.png = bytes(png)
        self.width, self.height = png_size(self.png)

    def to_json(self):
        return {"name": self.name, "png": base64.b64encode(self.png).decode("ascii")}

    @staticmethod
    def from_json(item, where):
        if not isinstance(item, dict) or "name" not in item or "png" not in item:
            raise ImageError("%s: expected {name, png}" % where)
        try:
            return Image(str(item["name"]), base64.b64decode(item["png"], validate=True))
        except (ValueError, TypeError) as e:           # (binascii.Error is a ValueError, and so is ImageError)
            raise ImageError("%s: %s" % (where, e))


def encode_png(rgba, width, height):
    """RGBA bytes (row by row from the top, straight alpha) -> PNG bytes, with nothing but zlib."""
    if len(rgba) != width * height * 4:
        raise ImageError("expected %d bytes of RGBA, got %d" % (width * height * 4, len(rgba)))

    def chunk(kind, body):
        c = struct.pack(">I", len(body)) + kind + body
        return c + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes(rgba[y * width * 4:(y + 1) * width * 4]) for y in range(height))
    return PNG_SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")


def decode_rgba(png):
    """PNG bytes -> (width, height, RGBA bytes with straight alpha, row by row from the top)."""
    w, h = png_size(png)
    try:
        from PIL import Image as PILImage
        import io
        im = PILImage.open(io.BytesIO(png)).convert("RGBA")
        return w, h, im.tobytes()
    except ImportError:
        pass
    from PyQt5 import QtGui
    img = QtGui.QImage.fromData(bytes(png), "PNG")
    if img.isNull():
        raise ImageError("could not decode the PNG")
    img = img.convertToFormat(QtGui.QImage.Format_RGBA8888)
    ptr = img.constBits()
    ptr.setsize(img.byteCount())
    stride = img.bytesPerLine()
    data = bytes(ptr)
    return w, h, b"".join(data[y * stride:y * stride + w * 4] for y in range(h))
