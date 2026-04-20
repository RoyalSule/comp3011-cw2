"""
test_indexer.py - Unit tests for the Indexer class.
"""

import json
import sys
import tempfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from indexer import Indexer

SIMPLE_HTML = """
<html>
  <body>
    <p>The quick brown fox jumps over the lazy dog.</p>
    <p>The dog sat on the mat.</p>
  </body>
</html>
"""

QUOTE_HTML = """
<html>
  <body>
    <span class="text">Life is what happens when you're busy making other plans.</span>
    <small class="author">John Lennon</small>
  </body>
</html>
"""

class TestTokenise:
    def setup_method(self):
        self.indexer = Indexer()

    def test_returns_list_of_strings(self):
        tokens = self.indexer._tokenise(SIMPLE_HTML)
        assert isinstance(tokens, list)
        assert all(isinstance(t, str) for t in tokens)

    def test_lowercase(self):
        html = "<html><body><p>Hello WORLD</p></body></html>"
        tokens = self.indexer._tokenise(html)
        assert "hello" in tokens
        assert "world" in tokens
        assert "Hello" not in tokens
        assert "WORLD" not in tokens

    def test_strips_punctuation(self):
        html = "<html><body><p>Hello, world!</p></body></html>"
        tokens = self.indexer._tokenise(html)
        assert "hello" in tokens
        assert "world" in tokens
        assert "hello," not in tokens
        assert "world!" not in tokens

    def test_script_tags_excluded(self):
        html = "<html><body><script>var x = 'secret';</script><p>visible</p></body></html>"
        tokens = self.indexer._tokenise(html)
        assert "secret" not in tokens
        assert "visible" in tokens

    def test_style_tags_excluded(self):
        html = "<html><head><style>.hidden { display:none }</style></head><body><p>shown</p></body></html>"
        tokens = self.indexer._tokenise(html)
        assert "hidden" not in tokens
        assert "shown" in tokens

    def test_empty_html(self):
        assert self.indexer._tokenise("") == []

    def test_no_text_content(self):
        html = "<html><body></body></html>"
        assert self.indexer._tokenise(html) == []

class TestIndexTokens:
    def setup_method(self):
        self.indexer = Indexer()

    def test_frequency_counted_correctly(self):
        tokens = ["the", "cat", "sat", "on", "the", "mat"]
        self.indexer._index_tokens("https://example.com/", tokens)
        assert self.indexer.index["the"]["https://example.com/"]["frequency"] == 2

    def test_positions_recorded(self):
        tokens = ["the", "cat", "the"]
        self.indexer._index_tokens("https://example.com/", tokens)
        assert self.indexer.index["the"]["https://example.com/"]["positions"] == [0, 2]

    def test_unique_words_get_own_entry(self):
        tokens = ["alpha", "beta", "gamma"]
        self.indexer._index_tokens("https://example.com/", tokens)
        assert set(self.indexer.index.keys()) == {"alpha", "beta", "gamma"}

    def test_multiple_pages_same_word(self):
        self.indexer._index_tokens("https://example.com/a", ["dog"])
        self.indexer._index_tokens("https://example.com/b", ["dog", "cat"])
        assert len(self.indexer.index["dog"]) == 2

class TestBuild:
    def setup_method(self):
        self.indexer = Indexer()

    def test_populates_index(self):
        pages = {"https://example.com/": SIMPLE_HTML}
        self.indexer.build(pages)
        assert len(self.indexer.index) > 0

    def test_resets_index_on_rebuild(self):
        pages1 = {"https://example.com/": "<html><body><p>alpha</p></body></html>"}
        pages2 = {"https://example.com/": "<html><body><p>beta</p></body></html>"}
        self.indexer.build(pages1)
        self.indexer.build(pages2)
        assert "alpha" not in self.indexer.index
        assert "beta" in self.indexer.index

    def test_empty_pages_dict_produces_empty_index(self):
        self.indexer.build({})
        assert self.indexer.index == {}

    def test_multiple_pages(self):
        pages = {
            "https://example.com/a": "<html><body><p>foo bar</p></body></html>",
            "https://example.com/b": "<html><body><p>bar baz</p></body></html>",
        }
        self.indexer.build(pages)
        assert len(self.indexer.index["bar"]) == 2

class TestSaveLoad:
    def setup_method(self):
        self.indexer = Indexer()
        pages = {"https://example.com/": SIMPLE_HTML}
        self.indexer.build(pages)

    def test_save_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "index.json"
            self.indexer.save(path)
            assert path.exists()

    def test_save_produces_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "index.json"
            self.indexer.save(path)
            with open(path) as fh:
                data = json.load(fh)
            assert isinstance(data, dict)

    def test_load_restores_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "index.json"
            self.indexer.save(path)

            new_indexer = Indexer()
            new_indexer.load(path)

            assert new_indexer.index == self.indexer.index

    def test_load_raises_if_file_missing(self):
        new_indexer = Indexer()
        with pytest.raises(FileNotFoundError):
            new_indexer.load(Path("/nonexistent/path/index.json"))

class TestQueryHelpers:
    def setup_method(self):
        self.indexer = Indexer()
        pages = {
            "https://example.com/a": "<html><body><p>The quick fox</p></body></html>",
            "https://example.com/b": "<html><body><p>The lazy dog</p></body></html>",
        }
        self.indexer.build(pages)

    def test_get_word_entry_found(self):
        entry = self.indexer.get_word_entry("the")
        assert entry is not None
        assert len(entry) == 2

    def test_get_word_entry_case_insensitive(self):
        assert self.indexer.get_word_entry("THE") == self.indexer.get_word_entry("the")

    def test_get_word_entry_not_found_returns_none(self):
        assert self.indexer.get_word_entry("zzznonsense") is None

    def test_get_pages_for_word_returns_set(self):
        pages = self.indexer.get_pages_for_word("fox")
        assert isinstance(pages, set)
        assert "https://example.com/a" in pages

    def test_get_pages_for_word_missing_returns_empty_set(self):
        assert self.indexer.get_pages_for_word("zzzmissing") == set()