import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'py'))

from interface import bible_interface as bible_verse_interface
from interface.bible_interface import BibleInterface

TRANSLATIONS_PAYLOAD = {"translations": [{"id": "BSB", "shortName": "BSB"}]}
BOOKS_PAYLOAD = {"books": [{"id": "GEN", "commonName": "Genesis", "numberOfChapters": 50}]}
CHAPTER_PAYLOAD = {
    "chapter": {
        "content": [
            {"type": "heading", "text": "The Creation"},
            {"type": "verse", "number": 1, "text": "In the beginning God created the heavens and the earth."},
        ]
    }
}


def _make_deterministic(monkeypatch):
    monkeypatch.setattr(bible_verse_interface.random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(bible_verse_interface.random, "randint", lambda a, b: 1)


@pytest.mark.asyncio
async def test_fetch_random_verse_success(monkeypatch):
    _make_deterministic(monkeypatch)

    async def fake_http_get(session, url):
        if url.endswith("available_translations.json"):
            return TRANSLATIONS_PAYLOAD
        if url.endswith("books.json"):
            return BOOKS_PAYLOAD
        return CHAPTER_PAYLOAD

    interface = BibleInterface(http_get=fake_http_get)
    verse = await interface.fetch_random_verse()

    assert verse is not None
    assert verse.text == "In the beginning God created the heavens and the earth."
    assert verse.reference == "Genesis 1:1 BSB"


@pytest.mark.asyncio
async def test_fetch_random_verse_returns_none_when_no_internet(monkeypatch):
    _make_deterministic(monkeypatch)

    async def fake_http_get(session, url):
        raise ConnectionError("no internet")

    interface = BibleInterface(http_get=fake_http_get)
    verse = await interface.fetch_random_verse()

    assert verse is None


@pytest.mark.asyncio
async def test_fetch_random_verse_returns_none_after_exhausting_bad_combos(monkeypatch):
    _make_deterministic(monkeypatch)
    call_count = 0

    async def fake_http_get(session, url):
        nonlocal call_count
        if url.endswith("available_translations.json"):
            return TRANSLATIONS_PAYLOAD
        call_count += 1
        raise RuntimeError("404 not found")

    interface = BibleInterface(http_get=fake_http_get)
    verse = await interface.fetch_random_verse()

    assert verse is None
    assert call_count == bible_verse_interface.BIBLE_VERSE.MAX_ATTEMPTS
