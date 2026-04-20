import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from crawler import Crawler

def make_page(links, body="Hello world"):
    anchors = "".join(f'<a href="{h}">link</a>' for h in links)
    return f"<html><body>{anchors}<p>{body}</p></body></html>"

class TestCleanUrl:
    def test_strips_fragment(self):
        assert Crawler._clean_url("https://example.com/page#section") == "https://example.com/page"
    def test_no_fragment_unchanged(self):
        url = "https://example.com/page"
        assert Crawler._clean_url(url) == url

class TestSameDomain:
    def setup_method(self):
        self.crawler = Crawler("https://quotes.toscrape.com/")
    def test_same_domain_accepted(self):
        assert self.crawler._same_domain("https://quotes.toscrape.com/page/2/")
    def test_different_domain_rejected(self):
        assert not self.crawler._same_domain("https://other.com/page")
    def test_ftp_rejected(self):
        assert not self.crawler._same_domain("ftp://quotes.toscrape.com/file")
    def test_subdomain_rejected(self):
        assert not self.crawler._same_domain("https://sub.quotes.toscrape.com/")

class TestGetLinks:
    def setup_method(self):
        self.crawler = Crawler("https://quotes.toscrape.com/")
    def test_returns_absolute_links(self):
        html = make_page(["/page/2/", "/author/einstein/"])
        links = self.crawler._get_links(html, "https://quotes.toscrape.com/")
        assert "https://quotes.toscrape.com/page/2/" in links
        assert "https://quotes.toscrape.com/author/einstein/" in links
    def test_filters_external_links(self):
        html = make_page(["https://other.com/"])
        assert self.crawler._get_links(html, "https://quotes.toscrape.com/") == []
    def test_empty_page(self):
        assert self.crawler._get_links("<html><body></body></html>", "https://quotes.toscrape.com/") == []
    def test_duplicate_links_preserved(self):
        html = make_page(["/page/2/", "/page/2/"])
        links = self.crawler._get_links(html, "https://quotes.toscrape.com/")
        assert links.count("https://quotes.toscrape.com/page/2/") == 2

class TestFetch:
    def setup_method(self):
        self.crawler = Crawler()
    @patch("crawler.requests.get")
    def test_returns_html_on_success(self, mock_get):
        mock_get.return_value = MagicMock(text="<html>OK</html>", raise_for_status=MagicMock())
        assert self.crawler._fetch("https://quotes.toscrape.com/") == "<html>OK</html>"
    @patch("crawler.requests.get")
    def test_returns_none_on_http_error(self, mock_get):
        import requests as req
        mock_get.side_effect = req.exceptions.HTTPError("404")
        assert self.crawler._fetch("https://quotes.toscrape.com/missing") is None
    @patch("crawler.requests.get")
    def test_returns_none_on_timeout(self, mock_get):
        import requests as req
        mock_get.side_effect = req.exceptions.Timeout()
        assert self.crawler._fetch("https://quotes.toscrape.com/slow") is None
    @patch("crawler.requests.get")
    def test_returns_none_on_connection_error(self, mock_get):
        import requests as req
        mock_get.side_effect = req.exceptions.ConnectionError()
        assert self.crawler._fetch("https://quotes.toscrape.com/gone") is None

class TestCrawl:
    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_follows_links(self, mock_get, mock_sleep):
        page1 = make_page(["/page/2/"])
        page2 = make_page([])

        def fake_get(url, **kw):
            r = MagicMock(raise_for_status=MagicMock())
            r.text = page2 if "/page/2" in url else page1
            return r

        mock_get.side_effect = fake_get
        pages = Crawler("https://quotes.toscrape.com/", politeness=0).crawl()
        assert len(pages) == 2

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_no_duplicate_visits(self, mock_get, mock_sleep):
        resp = MagicMock(text=make_page(["/"]), raise_for_status=MagicMock())
        mock_get.return_value = resp
        Crawler("https://quotes.toscrape.com/", politeness=0).crawl()
        assert mock_get.call_count == 1

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_skips_failed_pages(self, mock_get, mock_sleep):
        import requests as req
        mock_get.side_effect = req.exceptions.ConnectionError()
        assert Crawler("https://quotes.toscrape.com/", politeness=0).crawl() == {}

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_politeness_window_respected(self, mock_get, mock_sleep):
        page1 = make_page(["/page/2/"])
        page2 = make_page([])

        def fake_get(url, **kw):
            r = MagicMock(raise_for_status=MagicMock())
            r.text = page2 if "/page/2" in url else page1
            return r

        mock_get.side_effect = fake_get
        Crawler("https://quotes.toscrape.com/", politeness=6).crawl()
        mock_sleep.assert_called_with(6)