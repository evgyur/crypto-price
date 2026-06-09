#!/usr/bin/env python3
"""Quick /price command for crypto-price.

Usage: /price <SYMBOL> [duration]
Examples: /price HYPE 6h, /price BTC 1mo, /price SILVER 6mo
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
DEFAULT_SYMBOL = "HYPE"
DEFAULT_DURATION = "24h"
DURATION_RE = re.compile(
    r"^(?P<value>\d+(?:\.\d+)?)(?P<unit>months?|month|mons?|mo|weeks?|week|w|days?|day|d|hours?|hour|hrs?|hr|h|minutes?|minute|mins?|min|m|месяцев|месяца|месяц|мес|недель|недели|неделя|нед|дней|дня|день|д|часов|часа|час|ч|минут|минуты|минута|мин)?$",
    re.IGNORECASE,
)
UNIT_ALIASES = {
    "m": "m", "min": "m", "mins": "m", "minute": "m", "minutes": "m",
    "мин": "m", "минута": "m", "минуты": "m", "минут": "m",
    "h": "h", "hr": "h", "hrs": "h", "hour": "h", "hours": "h",
    "ч": "h", "час": "h", "часа": "h", "часов": "h",
    "d": "d", "day": "d", "days": "d", "д": "d", "день": "d", "дня": "d", "дней": "d",
    "w": "w", "week": "w", "weeks": "w", "нед": "w", "неделя": "w", "недели": "w", "недель": "w",
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


def _is_duration_token(tokens: list[str], idx: int) -> str | None:
    tok = tokens[idx].strip().lower()
    if re.match(r"^\d+(?:\.\d+)?$", tok) and idx + 1 < len(tokens):
        return _normalise_duration_token(tok, tokens[idx + 1])
    return _normalise_duration_token(tok)


def _collect_args(argv: list[str]) -> list[str]:
    args = list(argv)
    env_args = os.environ.get("HERMES_COMMAND_ARGS", "")
    if env_args.strip():
        try:
            args.extend(shlex.split(env_args))
        except ValueError:
            args.extend(env_args.split())
    return [a.strip() for a in args if a.strip()]


def _pick_symbol_duration(argv: list[str]) -> tuple[str, str]:
    args = _collect_args(argv)
    symbol = None
    duration = None
    skip_next = False
    for idx, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        dur = _is_duration_token(args, idx)
        if dur:
            duration = duration or dur
            if re.match(r"^\d+(?:\.\d+)?$", arg.strip()) and idx + 1 < len(args):
                skip_next = True
            continue
        if symbol is None:
            symbol = arg
    return (symbol or DEFAULT_SYMBOL).upper(), duration or DEFAULT_DURATION


def _print_price_with_chart(payload: dict, symbol: str, duration: str) -> None:
    text = payload.get("text_plain") or payload.get("text")
    if not text:
        price = payload.get("price") or payload.get("price_usdt")
        change = payload.get("change_period_percent")
        period = payload.get("duration") or duration
        currency = payload.get("currency") or "USD"
        if price is not None and change is not None:
            arrow = "⬆️" if float(change) >= 0 else "🔻"
            sign = "+" if float(change) >= 0 else ""
            text = f"{symbol}: ${float(price):.2f} {currency} {arrow} {sign}{float(change):.2f}% over {period}"
        else:
            text = f"{symbol}: price unavailable"

    print(text)
    source = payload.get("source")
    token_id = payload.get("token_id")
    if source or token_id:
        print(f"verify: source={source or 'n/a'} ticker={token_id or 'n/a'} duration={payload.get('duration') or duration}")
    chart_path = payload.get("chart_path")
    if chart_path and Path(str(chart_path)).is_file():
        print(f"MEDIA:{chart_path}")


def main() -> int:
    symbol, duration = _pick_symbol_duration(sys.argv[1:])
    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), symbol, duration],
            check=False,
            capture_output=True,
            text=True,
            timeout=35,
        )
    except subprocess.TimeoutExpired:
        print(f"{symbol}: price fetch timed out")
        return 0
    except Exception as exc:
        print(f"{symbol}: price fetch failed: {exc}")
        return 0

    raw = (proc.stdout or proc.stderr or "").strip()
    if not raw:
        print(f"{symbol}: price fetch returned no output")
        return 0
    json_line = raw.splitlines()[-1]
    try:
        payload = json.loads(json_line)
    except json.JSONDecodeError:
        print(raw.splitlines()[-1][:500])
        return 0
    if payload.get("error"):
        print(f"{symbol}: {payload.get('error')}")
        details = payload.get("details")
        if details:
            print(f"details: {details}")
        return 0
    _print_price_with_chart(payload, symbol, duration)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
