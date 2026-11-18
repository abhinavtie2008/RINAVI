import itertools

from app.modules.documents import extraction
from tests.factories import make_multipage_pdf


def test_pdf_parse_timeout_stops_extraction(monkeypatch) -> None:
    # The page and text limits bound how much is read, not how long it takes.
    # A deadline checked between pages keeps a slow document from holding the
    # single worker. The clock is injected so the test never sleeps.
    ticks = itertools.count(0.0, 1.0)
    monkeypatch.setattr(extraction.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(extraction, "PARSE_TIMEOUT_SECONDS", 0.0)

    pdf = make_multipage_pdf([["Applicant Name: Asha Devi"]])

    text, note = extraction.extract_text_from_pdf(pdf)

    assert note == "parse_timeout"
    assert text == ""


def test_pdf_under_the_deadline_is_unaffected(monkeypatch) -> None:
    monkeypatch.setattr(extraction.time, "monotonic", lambda: 0.0)

    pdf = make_multipage_pdf([["Applicant Name: Asha Devi"], ["Address: Delhi"]])

    text, note = extraction.extract_text_from_pdf(pdf)

    assert note is None
    assert "Asha Devi" in text
    assert "Address: Delhi" in text
