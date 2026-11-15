from app.modules.vault.routes import _content_disposition, _safe_download_name


def test_safe_download_name_strips_header_injection_chars() -> None:
    assert _safe_download_name('quote"name\r\nX-Evil: 1.txt') == "quotenameX-Evil 1.txt"
    assert _safe_download_name('!"\u00a3$%^') == "document"
    assert _safe_download_name("passport scan.pdf") == "passport scan.pdf"
    assert _safe_download_name("my file.tar.gz") == "my file.tar.gz"


def test_safe_download_name_is_ascii_for_regional_scripts() -> None:
    assert _safe_download_name("आय प्रमाण.pdf") == "document.pdf"
    assert _safe_download_name("आय-प्रमाण") == "document"


def test_content_disposition_carries_both_fallback_and_utf8_name() -> None:
    header = _content_disposition("आय प्रमाण.pdf")
    assert header.startswith('attachment; filename="document.pdf"')
    assert "filename*=UTF-8''%E0%A4%86%E0%A4%AF" in header
    # Starlette encodes header values as latin-1; the whole value must remain
    # ASCII or the response raises UnicodeEncodeError.
    assert header.isascii()
