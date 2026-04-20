import string
import logging
from indexer import Indexer

log = logging.getLogger(__name__)

class SearchEngine:
    def __init__(self, indexer: Indexer):
        self.indexer = indexer

    def print_word(self, word):
        if not word.strip():
            return "Please enter a word."
        entry = self.indexer.get_entry(word)
        if entry is None:
            return f"'{word}' wasn't found in the index."
        lines = [f"Results for '{self._clean(word)}' ({len(entry)} page(s)):"]
        for url, stats in sorted(entry.items()):
            lines.append(f"  URL       : {url}")
            lines.append(f"  Frequency : {stats['frequency']}")
            lines.append(f"  Positions : {stats['positions']}")
        return "\n".join(lines)

    def find_pages(self, query):
        terms = self._parse(query)
        if not terms:
            return "Please enter at least one search term."
        matches = self.indexer.get_pages(terms[0])
        for term in terms[1:]:
            matches &= self.indexer.get_pages(term)
        if not matches:
            return f"No pages found for: {', '.join(terms)}"
        lines = [f"Pages containing {' + '.join(repr(t) for t in terms)}:"]
        for url in sorted(matches):
            lines.append(f"  {url}")
        return "\n".join(lines)

    def _parse(self, query):
        seen = set()
        terms = []
        for word in query.split():
            w = self._clean(word)
            if w and w not in seen:
                seen.add(w)
                terms.append(w)
        return terms

    @staticmethod
    def _clean(word):
        return word.lower().strip(string.punctuation)