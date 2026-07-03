"""Discover construction-tech organizations on GitHub via topic search.

Searches public repositories tagged with construction-tech topics, then
resolves each unique repo owner's profile (company, blog, location) for
later manual review.
"""

import logging
import os
import time
from typing import Any

import requests
from common import JsonlWriter, output_path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

API_BASE = "https://api.github.com"
TOPICS = ["construction", "bim", "cim", "contech", "kensetsu"]
REQUEST_INTERVAL_SECONDS = 2.0
TIMEOUT_SECONDS = 15
HTTP_FORBIDDEN = 403


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        logger.warning(
            "GITHUB_TOKEN not set; unauthenticated rate limits are very low "
            "(10 search req/min, 60 core req/hour)"
        )
    return headers


def _get(url: str, headers: dict[str, str], params: dict[str, Any] | None = None) -> dict[str, Any]:
    """GET with a one-time wait-and-retry if we hit GitHub's rate limit."""
    response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT_SECONDS)
    rate_limited = (
        response.status_code == HTTP_FORBIDDEN
        and response.headers.get("X-RateLimit-Remaining") == "0"
    )
    if rate_limited:
        reset_at = int(response.headers.get("X-RateLimit-Reset", "0"))
        wait_seconds = max(reset_at - time.time(), 0) + 1
        logger.warning("rate limited, sleeping %.0fs until reset", wait_seconds)
        time.sleep(wait_seconds)
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    result: dict[str, Any] = response.json()
    return result


def search_repos_by_topic(topic: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    """Search public repositories tagged with the given topic."""
    result = _get(
        f"{API_BASE}/search/repositories",
        headers,
        params={"q": f"topic:{topic}", "per_page": 30},
    )
    items: list[dict[str, Any]] = result.get("items", [])
    return items


def fetch_owner_profile(login: str, headers: dict[str, str]) -> dict[str, Any]:
    """Fetch a user/organization profile (the same endpoint covers both)."""
    return _get(f"{API_BASE}/users/{login}", headers)


def main() -> None:
    """Search GitHub for construction-tech repositories and their owners."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv()
    headers = _headers()

    repos_path = output_path("github", "repos")
    owners_path = output_path("github", "owners")
    seen_owners: set[str] = set()

    with JsonlWriter(repos_path) as repo_writer, JsonlWriter(owners_path) as owner_writer:
        for topic in TOPICS:
            logger.info("searching topic:%s", topic)
            try:
                repos = search_repos_by_topic(topic, headers)
            except requests.HTTPError:
                logger.exception("search failed for topic:%s", topic)
                continue
            for repo in repos:
                repo_writer.write({"topic": topic, "repo": repo})
                owner = repo.get("owner") or {}
                login = owner.get("login")
                if not login or login in seen_owners:
                    continue
                seen_owners.add(login)
                time.sleep(REQUEST_INTERVAL_SECONDS)
                try:
                    profile = fetch_owner_profile(login, headers)
                except requests.HTTPError:
                    logger.exception("profile fetch failed for %s", login)
                    continue
                owner_writer.write({"login": login, "profile": profile})
            time.sleep(REQUEST_INTERVAL_SECONDS)
    logger.info("done")


if __name__ == "__main__":
    main()
