"""Search Tavily for other people's curated construction-tech vendor lists.

Unlike scrape_tavily.py (a broad keyword sweep for individual companies),
this targets meta-resources: chaos maps, comparison round-ups, and "matome"
articles that someone else has already curated. Results are dumped raw for
manual triage; promising hits get followed up individually, the same way
the 2024 chaos map from 建築現場の知恵袋 was.
"""

import logging
import os

from dotenv import load_dotenv
from tavily import TavilyClient

from common import JsonlWriter, output_path

logger = logging.getLogger(__name__)

QUERIES = [
    "建設テック カオスマップ",
    "建設DX カオスマップ",
    "contech カオスマップ",
    "建設業 DXツール カオスマップ",
    "建設 SaaS カオスマップ",
    "施工管理 SaaS 比較 まとめ",
    "建設テック スタートアップ 一覧",
    "建設DXツール 比較 まとめ",
    "ConTech 国内 企業 一覧",
    "建設テック カオスマップ 2025年版",
    "建設テック カオスマップ 2023年版",
    "建設業界 SaaS カオスマップ",
]


def run_search(client: TavilyClient, queries: list[str], writer: JsonlWriter) -> None:
    """Run each meta-search query against Tavily and append raw results via writer."""
    for i, query in enumerate(queries, start=1):
        logger.info("[%d/%d] %s", i, len(queries), query)
        try:
            response = client.search(query=query, search_depth="basic", max_results=10)
        except Exception:
            logger.exception("query failed: %s", query)
            continue
        writer.write({"query": query, "response": response})


def main() -> None:
    """Search Tavily for construction-tech chaos maps and comparison round-ups."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv()
    api_key = os.environ["TAVILY_API_KEY"]
    client = TavilyClient(api_key=api_key)

    path = output_path("tavily_maps", "sweep")
    logger.info("running %d queries, writing to %s", len(QUERIES), path)
    with JsonlWriter(path) as writer:
        run_search(client, QUERIES, writer)
    logger.info("done")


if __name__ == "__main__":
    main()
