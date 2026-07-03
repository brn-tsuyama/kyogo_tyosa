# kyogo_tyosa

Research pipeline for finding and profiling Japanese companies that sell software
products to construction companies (建設会社向けソフトウェア企業調査).

## Setup

```
uv sync
cp .env.example .env   # fill in TAVILY_API_KEY, optionally GITHUB_TOKEN
```

## Source tracking

`sources.yaml` is the index of every source considered for this research, split into:

- **auto** — sources a script can collect (further split into *discovery* sources that
  surface new company names, and *enrichment* sources used to verify/fill in details
  for companies already found elsewhere).
- **curated** — one-off compilations someone else already curated (chaos maps,
  comparison articles). These are transcribed by hand into `data/curated/` rather than
  scraped, either because there's no repeatable script to write or because the site's
  `robots.txt` disallows automated collection.
- **manual** — sources with ToS/robots.txt that prohibit automated collection, or that
  require a paid account. Deprioritized; only touched opportunistically.

Check a source's `notes` field in `sources.yaml` before writing a new scraper against
it — several sites were investigated and found impractical or off-limits (documented
there instead of being retried).

## Scripts

Each script is a standalone entry point (`uv run <script>.py`), writing timestamped
JSONL into `data/raw/<source>/`:

| Script | Discovers |
|---|---|
| `scrape_jstartup.py` | J-Startup (METI-certified startup) directory listing |
| `scrape_github.py` | GitHub orgs/repos tagged with construction-tech topics (low signal — mostly global OSS projects, see `sources.yaml`) |
| `scrape_tavily.py` | Keyword-sweep search for individual companies |
| `scrape_tavily_maps.py` | Meta-search for other people's chaos maps / comparison round-ups |

`data/curated/*.jsonl` holds hand-transcribed entries from curated compilations found
via `scrape_tavily_maps.py` or supplied directly by the user.

`build_master_list.py` merges every `data/curated/*.jsonl` and the latest
`data/raw/jstartup/*.jsonl` into one deduplicated, priority-ranked candidate list
(`data/master_candidates.json`), cross-referencing `data/report/競合分析.xlsx` so
already-profiled companies aren't re-researched.

## Competitor profiling

Candidates from `data/master_candidates.json` get researched (via WebSearch, in
batches) into JSON records matching the schema below, saved under
`data/report/batches/*.json`:

```json
{
  "product_name": "...", "company_name": "...", "field": "...",
  "scale": "大手|中堅|中小|小規模|全規模", "industry": "...", "description": "...",
  "functions": {"施工管理": "◎|○|△|×", "原価管理": "...", "CAD・BIM": "...",
                 "労務": "...", "経理": "...", "案件管理": "...", "調達": "...",
                 "顧客管理": "...", "センシング": "..."},
  "ai_status": "◎|○|△|×", "ai_features": "...", "ai_notes": "...",
  "confidence": "...", "research_sources": ["..."], "research_date": "YYYY-MM-DD"
}
```

`write_research_to_excel.py` rebuilds `data/report/競合分析2.xlsx` from every
`data/report/batches/batch*.json` file (idempotent — reruns fully replace the sheet
contents rather than appending). `data/report/batches/rejected/` holds batches that
turned out to be low quality and were excluded from the pipeline.

## Legal notes

Before adding a new scraper, check the target's `robots.txt` and ToS. This project
treats `Disallow: /` (or a named block on AI crawlers like `ClaudeBot`) as a hard
no — see `sources.yaml` for examples of sites ruled out this way.
