"""Keyword-sweep discovery via the Tavily Search API.

Runs a keyword sweep against the Tavily Search API to discover companies
selling software products to construction companies, and dumps the raw
results to a JSONL file for later review.
"""

import itertools
import logging
import os
import time

from common import JsonlWriter, output_path
from dotenv import load_dotenv
from tavily import TavilyClient

logger = logging.getLogger(__name__)

DOMAIN_TERMS = ["建設", "工事", "施工", "建築"]
PRODUCT_TERMS = ["管理システム", "DX", "SaaS", "ICT", "業務システム", "クラウドサービス"]
SEGMENT_TERMS = ["中小企業向け", "新規参入", "スタートアップ", "ベンチャー企業"]

REQUEST_INTERVAL_SECONDS = 0.5


def build_queries() -> list[str]:
    """Build the keyword-sweep queries from the term axes."""
    return [
        f"{domain} {product} {segment}"
        for domain, product, segment in itertools.product(
            DOMAIN_TERMS, PRODUCT_TERMS, SEGMENT_TERMS
        )
    ]


def run_sweep(client: TavilyClient, queries: list[str], writer: JsonlWriter) -> None:
    """Run each query against Tavily and append the raw results via writer."""
    for i, query in enumerate(queries, start=1):
        logger.info("[%d/%d] %s", i, len(queries), query)
        try:
            response = client.search(query=query, search_depth="basic")
        except Exception:
            logger.exception("query failed: %s", query)
            continue
        writer.write({"query": query, "response": response})
        time.sleep(REQUEST_INTERVAL_SECONDS)


def main() -> None:
    """Run the Tavily keyword-sweep workflow."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv()
    api_key = os.environ["TAVILY_API_KEY"]
    client = TavilyClient(api_key=api_key)

    queries = build_queries()
    path = output_path("tavily", "sweep")

    logger.info("running %d queries, writing to %s", len(queries), path)
    with JsonlWriter(path) as writer:
        run_sweep(client, queries, writer)
    logger.info("done")


if __name__ == "__main__":
    main()
