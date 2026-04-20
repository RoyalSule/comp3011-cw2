"""
test_search.py - Unit tests for the SearchEngine class.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from indexer import Indexer
from search import SearchEngine

def build_engine(pages: dict[str, str]) -> SearchEngine:
    """Convenience: build an Indexer from pages and wrap it in a SearchEngine."""
    indexer = Indexer()
    indexer.build(pages)
    return SearchEngine(indexer)

PAGES = {
    "https://quotes.toscrape.com/": (
        "<html><body><p>The world as we have created it is a process of our thinking.</p></body></html>"
    ),
    "https://quotes.toscrape.com/page/2/": (
        "<html><body><p>It is our choices that show what we truly are far more than our abilities.</p></body></html>"
    ),
    "https://quotes.toscrape.com/page/3/": (
        "<html><body><p>There are only two ways to live your life.</p></body></html>"
    ),
}

class TestPrintWord:
    def setup_method(self):
        self.engine = build_engine(PAGES)

    def test_found_word_shows_url(self):
        output = self.engine.print_word("world")
        assert "quotes.toscrape.com" in output

    def test_found_word_shows_frequency(self):
        output = self.engine.print_word("our")
        assert "Frequency" in output

    def test_found_word_shows_positions(self):
        output = self.engine.print_word("the")
        assert "Positions" in output

    def test_missing_word_returns_not_found_message(self):
        output = self.engine.print_word("zzznonsense")
        assert "wasn't found" in output

    def test_case_insensitive(self):
        lower = self.engine.print_word("world")
        upper = self.engine.print_word("WORLD")
        assert lower == upper

    def test_empty_string_returns_error(self):
        output = self.engine.print_word("")
        assert "Please enter" in output

    def test_whitespace_only_returns_error(self):
        output = self.engine.print_word("   ")
        assert "Please enter" in output

class TestFindPagesSingleTerm:
    def setup_method(self):
        self.engine = build_engine(PAGES)

    def test_word_on_one_page(self):
        output = self.engine.find_pages("choices")
        assert "page/2" in output

    def test_word_on_multiple_pages(self):
        output = self.engine.find_pages("our")
        assert "toscrape.com/" in output
        assert "page/2" in output

    def test_missing_word_returns_no_pages_message(self):
        output = self.engine.find_pages("zzzmissing")
        assert "no pages" in output.lower()

    def test_case_insensitive_search(self):
        lower = self.engine.find_pages("world")
        upper = self.engine.find_pages("WORLD")
        assert lower == upper

class TestFindPagesMultiWord:
    def setup_method(self):
        self.engine = build_engine(PAGES)

    def test_two_terms_on_same_page(self):
        output = self.engine.find_pages("choices abilities")
        assert "page/2" in output

    def test_two_terms_on_different_pages_returns_empty(self):
        output = self.engine.find_pages("world choices")
        assert "no pages" in output.lower()

    def test_three_terms_intersection(self):
        output = self.engine.find_pages("our choices are")
        assert "page/2" in output
        lines = [l.strip() for l in output.splitlines() if l.strip().startswith("http")]
        assert all("page/2" in url for url in lines), (
            f"Expected only page/2, got: {lines}"
        )

    def test_duplicate_terms_treated_as_one(self):
        single = self.engine.find_pages("our")
        duplicate = self.engine.find_pages("our our")
        assert single == duplicate

    def test_mixed_case_multi_word(self):
        output = self.engine.find_pages("CHOICES Abilities")
        assert "page/2" in output

class TestFindPagesEdgeCases:
    def setup_method(self):
        self.engine = build_engine(PAGES)

    def test_empty_query_returns_error(self):
        output = self.engine.find_pages("")
        assert "Please enter" in output

    def test_whitespace_only_query_returns_error(self):
        output = self.engine.find_pages("   ")
        assert "Please enter" in output

    def test_punctuation_stripped_from_query(self):
        with_punct = self.engine.find_pages("world.")
        without_punct = self.engine.find_pages("world")
        assert with_punct == without_punct

    def test_empty_index_returns_no_pages(self):
        empty_engine = SearchEngine(Indexer())
        output = empty_engine.find_pages("anything")
        assert "no pages" in output.lower()