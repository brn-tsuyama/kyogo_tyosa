"""Write researched product JSON batches into 競合分析2.xlsx's three sheets."""

import json
import logging
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

logger = logging.getLogger(__name__)

BATCHES_DIR = Path("data/report/batches")
WORKBOOK_PATH = Path("data/report/競合分析2.xlsx")

COMPETITOR_HEADERS = ["商品名", "社名", "分野", "規模", "業界", "説明", "確信度・根拠メモ"]
FUNCTION_KEYS = [
    "施工管理",
    "原価管理",
    "CAD・BIM",
    "労務",
    "経理",
    "案件管理",
    "調達",
    "顧客管理",
    "センシング",
]
FUNCTION_HEADERS = ["プロダクト名", *FUNCTION_KEYS, "確信度・根拠メモ"]
AI_HEADERS = [
    "プロダクト名",
    "社名",
    "AI実装状況",
    "主なAI機能・適用領域",
    "解説・特記事項",
    "確信度・根拠メモ",
]


def load_records() -> list[dict[str, Any]]:
    """Load and concatenate every batch JSON file in order."""
    records: list[dict[str, Any]] = []
    for path in sorted(BATCHES_DIR.glob("batch*.json")):
        records.extend(json.loads(path.read_text(encoding="utf-8")))
    return records


def reset_sheet(ws: Worksheet, headers: list[str]) -> None:
    """Clear all rows and write a fresh header row."""
    ws.delete_rows(1, ws.max_row)
    ws.append(headers)


def write_records(records: list[dict[str, Any]]) -> None:
    """Rewrite the 競合リスト, 機能, and AI活用動向 sheets from scratch."""
    wb = openpyxl.load_workbook(WORKBOOK_PATH)

    competitor_ws = wb["競合リスト"]
    functions_ws = wb["機能"]
    ai_ws = wb["AI活用動向"]

    reset_sheet(competitor_ws, COMPETITOR_HEADERS)
    reset_sheet(functions_ws, FUNCTION_HEADERS)
    reset_sheet(ai_ws, AI_HEADERS)

    for rec in records:
        competitor_ws.append(
            [
                rec["product_name"],
                rec["company_name"],
                rec["field"],
                rec["scale"],
                rec["industry"],
                rec["description"],
                rec["confidence"],
            ]
        )

        functions = rec["functions"]
        functions_ws.append(
            [
                rec["product_name"],
                *(functions[key] for key in FUNCTION_KEYS),
                rec["confidence"],
            ]
        )

        ai_ws.append(
            [
                rec["product_name"],
                rec["company_name"],
                rec["ai_status"],
                rec["ai_features"],
                rec["ai_notes"],
                rec["confidence"],
            ]
        )

    wb.save(WORKBOOK_PATH)
    logger.info("wrote %d records to %s", len(records), WORKBOOK_PATH)


def main() -> None:
    """Load all research batches and write them into the workbook."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    records = load_records()
    write_records(records)


if __name__ == "__main__":
    main()
