MAX_UPLOAD_BYTES = 10 * 1024 * 1024

_PDF_MAGIC = b"%PDF-"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"
_ALLOWED_CONTROL = {"\t", "\n", "\r"}


def sniff_content_type(data: bytes) -> str | None:
    if data.startswith(_PDF_MAGIC):
        return "application/pdf"
    if data.startswith(_PNG_MAGIC):
        return "image/png"
    if data.startswith(_JPEG_MAGIC):
        return "image/jpeg"
    if _is_utf8_text(data):
        return "text/plain"
    return None


def _is_utf8_text(data: bytes) -> bool:
    if not data:
        return False
    try:
        decoded = data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    # Binary payloads can decode as UTF-8; reject C0 controls that text never contains.
    return all(
        char in _ALLOWED_CONTROL or ord(char) >= 0x20 for char in decoded
    )
