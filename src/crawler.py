import time
import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

BASE_URL = "https://quotes.toscrape.com/"
POLITENESS = 6

class Crawler:
    def __init__(self, base_url=BASE_URL, politeness=POLITENESS):
        self.base_url = base_url
        self.politeness = politeness
        self.pages = {}
        self.domain = urlparse(base_url).netloc

    def crawl(self):
        self.pages = {}
        visited = set()
        queue = [self.base_url]

        while queue:
            url = self._clean_url(queue.pop(0))
            if url in visited:
                continue

            visited.add(url)
            html = self._fetch(url)
            if html is None:
                continue

            self.pages[url] = html
            log.info("Crawled %s (%d pages so far)", url, len(self.pages))

            for link in self._get_links(html, url):
                if link not in visited:
                    queue.append(link)

            if queue:
                time.sleep(self.politeness)

        log.info("Done. %d pages collected.", len(self.pages))
        return self.pages

    def _fetch(self, url):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            return r.text
        except requests.exceptions.RequestException as e:
            log.warning("Skipping %s: %s", url, e)
            return None

    def _get_links(self, html, current_url):
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for tag in soup.find_all("a", href=True):
            url = self._clean_url(urljoin(current_url, tag["href"]))
            if self._same_domain(url):
                links.append(url)
        return links

    def _same_domain(self, url):
        p = urlparse(url)
        return p.netloc == self.domain and p.scheme in ("http", "https")

    @staticmethod
    def _clean_url(url):
        return urlparse(url)._replace(fragment="").geturl()
