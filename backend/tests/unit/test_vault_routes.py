from app.modules.vault.routes import _safe_download_name


def test_safe_download_name_strips_header_injection_chars() -> None:
    assert _safe_download_name('quote"name\r\nX-Evil: 1.txt') == "quotenameX-Evil 1.txt"
    assert _safe_download_name('!"£$%^') == "document"
    assert _safe_download_name("passport scan.pdf") == "passport scan.pdf"
