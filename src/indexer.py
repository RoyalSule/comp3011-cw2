import json
import logging
import string
from pathlib import Path

from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

INDEX_PATH = Path(__file__).parent.parent / "data" / "index.json"

class Indexer:
    def __init__(self):
        # { word: { url: { frequency: int, positions: [int] } } }
        self.index = {}

    def build(self, pages):
        self.index = {}
        for url, html in pages.items():
            tokens = self._tokenise(html)
            self._add_to_index(url, tokens)
            log.debug("Indexed %s (%d tokens)", url, len(tokens))
        log.info("Built index: %d unique words from %d pages.", len(self.index), len(pages))

    def save(self, path=INDEX_PATH):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
        log.info("Index saved to %s", path)

    def load(self, path=INDEX_PATH):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"No index at '{path}'. Run 'build' first.")
        with open(path, "r", encoding="utf-8") as f:
            self.index = json.load(f)
        log.info("Index loaded: %d words.", len(self.index))

    def get_entry(self, word):
        return self.index.get(self._clean(word))

    def get_pages(self, word):
        entry = self.get_entry(word)
        return set(entry.keys()) if entry else set()

    def _tokenise(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        tokens = []
        for raw in soup.get_text(separator=" ").lower().split():
            word = raw.strip(string.punctuation)
            if word:
                tokens.append(word)
        return tokens

    def _add_to_index(self, url, tokens):
        for pos, word in enumerate(tokens):
            self.index.setdefault(word, {}).setdefault(url, {"frequency": 0, "positions": []})
            self.index[word][url]["frequency"] += 1
            self.index[word][url]["positions"].append(pos)

    @staticmethod
    def _clean(word):
        return word.lower().strip(string.punctuation)
