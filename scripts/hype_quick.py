#!/usr/bin/env python3
"""Quick /hype command owned by the crypto-price skill.

Prints HYPE price text plus a MEDIA chart tag for Hermes/OpenClaw gateways.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "get_price_chart.py"
DEFAULT_DURATION = "24h"
DURATION_RE = re.compile(
    r"^(?P<value>\d+(?:\.\d+)?)(?P<unit>months?|month|mons?|mo|weeks?|week|w|days?|day|d|hours?|hour|hrs?|hr|h|minutes?|minute|mins?|min|m|месяцев|месяца|месяц|мес|недель|недели|неделя|нед|дней|дня|день|д|часов|часа|час|ч|минут|минуты|минута|мин)?$",
    re.IGNORECASE,
)
UNIT_ALIASES = {
    # minutes
    "m": "m", "min": "m", "mins": "m", "minute": "m", "minutes": "m",
    "мин": "m", "минута": "m", "минуты": "m", "минут": "m",
    # hours
    "h": "h", "hr": "h", "hrs": "h", "hour": "h", "hours": "h",
    "ч": "h", "час": "h", "часа": "h", "часов": "h",
    # days
    "d": "d", "day": "d", "days": "d",
    "д": "d", "день": "d", "дня": "d", "дней": "d",
    # weeks
    "w": "w", "week": "w", "weeks": "w",
    "нед": "w", "неделя": "w", "недели": "w", "недель": "w",
    # months are chart periods, not calendar arithmetic: 1mo = 30d.
    "mo": "mo", "mon": "mo", "mons": "mo", "month": "mo", "months": "mo",
    "мес": "mo", "месяц": "mo", "месяца": "mo", "месяцев": "mo",
}


def _format_value(value: str) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


def _normalise_duration_token(value_token: str, unit_token: str | None = None) -> str | None:
    compact = f"{value_token}{unit_token or ''}".strip().lower()
    match = DURATION_RE.match(compact)
    if not match:
        return None
    unit = (match.group("unit") or "h").lower()
    canonical_unit = UNIT_ALIASES.get(unit)
    if not canonical_unit:
        return None
    return f"{_format_value(match.group('value'))}{canonical_unit}"


def _pick_duration(argv: list[str]) -> str:
    candidates: list[str] = []
    candidates.extend(argv)
    env_args = os.environ.get("HERMES_COMMAND_ARGS", "")
    if env_args.strip():
        try:
            candidates.extend(shlex.split(env_args))
        except ValueError:
            candidates.extend(env_args.split())

    cleaned = [arg.strip().lower() for arg in candidates if arg.strip()]
    for idx, arg in enumerate(cleaned):
        if re.match(r"^\d+(?:\.\d+)?$", arg) and idx + 1 < len(cleaned):
            duration = _normalise_duration_token(arg, cleaned[idx + 1])
            if duration:
                return duration
        duration = _normalise_duration_token(arg)
        if duration:
            return duration
    return DEFAULT_DURATION


def _print_price_with_chart(payload: dict, duration: str) -> None:
    text = payload.get("text_plain") or payload.get("text")
    if not text:
        price = payload.get("price") or payload.get("price_usdt")
        change = payload.get("change_period_percent")
        period = payload.get("duration") or duration
        if price is not None and change is not None:
            arrow = "⬆️" if float(change) >= 0 else "⬇️"
            sign = "+" if float(change) >= 0 else ""
            text = f"HYPE: ${float(price):.2f} USD {arrow} {sign}{float(change):.2f}% over {period}"
        else:
            text = "HYPE: price unavailable"

    print(text)

    chart_path = payload.get("chart_path")
    if chart_path and Path(str(chart_path)).is_file():
        print(f"MEDIA:{chart_path}")


def main() -> int:
    duration = _pick_duration(sys.argv[1:])

    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "HYPE", duration],
            check=False,
            capture_output=True,
            text=True,
            timeout=25,
        )
    except subprocess.TimeoutExpired:
        print("HYPE: price fetch timed out")
        return 0
    except Exception as exc:
        print(f"HYPE: price fetch failed: {exc}")
        return 0

    raw = (proc.stdout or proc.stderr or "").strip()
    if not raw:
        print("HYPE: price fetch returned no output")
        return 0

    # Some chart backends can print warnings before JSON. Use the final JSON line.
    json_line = raw.splitlines()[-1]
    try:
        payload = json.loads(json_line)
    except json.JSONDecodeError:
        print(raw.splitlines()[-1][:500])
        return 0

    if payload.get("error"):
        print(f"HYPE: {payload.get('error')}")
        return 0

    _print_price_with_chart(payload, duration)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
