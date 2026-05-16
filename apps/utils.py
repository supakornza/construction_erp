import io

try:
    import pillow_heif as _pillow_heif
    _pillow_heif.register_heif_opener()
except ImportError:
    pass


def image_to_jpeg_bytes(path_or_file):
    """Return a JPEG BytesIO from any image file (HEIC, PNG, JPG, etc.)."""
    from PIL import Image as PILImage
    img = PILImage.open(path_or_file)
    img.load()
    if img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    buf.seek(0)
    return buf
