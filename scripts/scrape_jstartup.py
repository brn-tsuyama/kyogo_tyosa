"""Discover companies via the J-Startup (METI-certified startups) directory.

The full list is server-rendered on a single page, so this is a plain
HTML scrape (no JS execution, no pagination) into a JSONL dump for later
keyword-based filtering.
"""

import logging
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from common import JsonlWriter, output_path

logger = logging.getLogger(__name__)

LIST_URL = "https://www.j-startup.go.jp/startups/"
BASE_URL = "https://www.j-startup.go.jp"
TIMEOUT_SECONDS = 15


def fetch_listing_html() -> str:
    """Fetch the raw HTML of the startups listing page."""
    response = requests.get(LIST_URL, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.text


def parse_entries(html: str) -> list[dict[str, Any]]:
    """Extract each startup's name, detail URL, and category tags."""
    soup = BeautifulSoup(html, "html.parser")
    entries: list[dict[str, Any]] = []
    for anchor in soup.select("#startupslist .item > a[data-cats]"):
        href = anchor.get("href")
        name_tag = anchor.select_one(".company-name")
        if not isinstance(href, str) or name_tag is None:
            continue
        cats = anchor.get("data-cats", "")
        categories = [c for c in str(cats).split("/") if c]
        entries.append(
            {
                "name": name_tag.get_text(strip=True),
                "url": urljoin(BASE_URL, href),
                "categories": categories,
            }
        )
    return entries


def main() -> None:
    """Scrape the J-Startup directory and write results to a JSONL file."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    html = fetch_listing_html()
    entries = parse_entries(html)
    logger.info("parsed %d entries", len(entries))

    path = output_path("jstartup", "listing")
    with JsonlWriter(path) as writer:
        for entry in entries:
            writer.write(entry)
    logger.info("done")


if __name__ == "__main__":
    main()
