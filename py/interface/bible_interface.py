from app_logging import get_adapter

logger = get_adapter("bible_verse", "startup")
logger.info("Importing bible verse interface...")

import random
from dataclasses import dataclass

import aiohttp

from globals import BIBLE_VERSE


@dataclass
class BibleVerse:
    text: str
    reference: str


class BibleInterface:
    """Fetches a truly random Bible verse via the Free Use Bible API (bible.helloao.org)."""

    def __init__(self, http_get=None, *args, **kwargs):
        self.__http_get = http_get or self._default_http_get

    async def _default_http_get(self, session, url):
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def _get_json(self, session, url):
        return await self.__http_get(session, url)

    def _pick_random_verse(self, translation, book, chapter_number, chapter_data):
        content = chapter_data.get("chapter", {}).get("content", [])
        verses = [item for item in content if item.get("type") == "verse"]
        if not verses:
            return None

        verse = random.choice(verses)
        shortName = translation.get("shortName") or translation.get("id")
        reference = f"{book['commonName']} {chapter_number}:{verse['number']} {shortName}"
        return BibleVerse(text=verse["text"], reference=reference)

    async def fetch_random_verse(self):
        """Random translation -> random book -> random chapter -> random verse, retrying bad combos.

        Returns None if the API is unreachable at all (treated as "no internet") or if every
        retry produces an unusable combo, so callers can silently skip the verse screen.
        """
        timeout = aiohttp.ClientTimeout(total=BIBLE_VERSE.REQUEST_TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                translations_payload = await self._get_json(
                    session, f"{BIBLE_VERSE.API_BASE_URL}/available_translations.json"
                )
                translations = translations_payload["translations"]
                # Restrict to English translations: the API also serves scripts (Devanagari,
                # Ethiopic, etc.) that the device's installed fonts can't render, which shows
                # as tofu boxes instead of text.
                english_translations = [t for t in translations if t.get("language") == "eng"]
                if english_translations:
                    translations = english_translations
            except Exception as exc:
                logger.warning(f"Could not reach Bible API, skipping verse screen: {exc}", category="startup")
                return None

            for attempt in range(BIBLE_VERSE.MAX_ATTEMPTS):
                try:
                    translation = random.choice(translations)
                    books_payload = await self._get_json(
                        session, f"{BIBLE_VERSE.API_BASE_URL}/{translation['id']}/books.json"
                    )
                    book = random.choice(books_payload["books"])
                    chapter_number = random.randint(1, book["numberOfChapters"])
                    chapter_data = await self._get_json(
                        session,
                        f"{BIBLE_VERSE.API_BASE_URL}/{translation['id']}/{book['id']}/{chapter_number}.simple.json",
                    )
                    verse = self._pick_random_verse(translation, book, chapter_number, chapter_data)
                    if verse is not None:
                        return verse
                except Exception as exc:
                    logger.warning(f"Bad random verse pick on attempt {attempt + 1}: {exc}", category="startup")

            logger.warning("Exhausted retries fetching a random verse, skipping verse screen.", category="startup")
            return None


bibleInterface = BibleInterface()
