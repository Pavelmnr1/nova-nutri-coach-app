from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime
from typing import Any


logger = logging.getLogger("nutrition_bot")


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def dumps_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=True)


def loads_json(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def today_utc_date() -> date:
    return datetime.utcnow().date()


def bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items if item)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_clean_summary_text(raw_text: str | None) -> str | None:
    if not raw_text:
        return None

    text = raw_text.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            for key in ("summary", "text", "message"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return normalize_whitespace(value)
        if isinstance(data, str) and data.strip():
            return normalize_whitespace(data)
    except json.JSONDecodeError:
        pass

    if "{" in text and "}" in text:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            try:
                data = json.loads(snippet)
                if isinstance(data, dict):
                    for key in ("summary", "text", "message"):
                        value = data.get(key)
                        if isinstance(value, str) and value.strip():
                            return normalize_whitespace(value)
            except json.JSONDecodeError:
                pass

    cleaned = re.sub(r"[{}[\]`]+", " ", text)
    cleaned = normalize_whitespace(cleaned)
    return cleaned or None


def format_confidence_percent(confidence: float | None) -> str | None:
    if confidence is None:
        return None
    percent = round(confidence * 100) if confidence <= 1 else round(confidence)
    return f"{percent}%"


def normalize_option_text(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum() or char.isspace()).strip()


def match_option(answer: str, options: list[str]) -> str | None:
    normalized_answer = normalize_option_text(answer)
    if not normalized_answer:
        return None

    for option in options:
        normalized_option = normalize_option_text(option)
        if normalized_answer == normalized_option:
            return option
        if normalized_answer in normalized_option or normalized_option in normalized_answer:
            return option
    return None
