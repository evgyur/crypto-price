#!/usr/bin/env python3
"""Quick /spaghetti command for crypto-price.

Usage: /spaghetti <SYMBOL...> [duration]
Example: /spaghetti SP500 GOLD SILVER 6mo
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "get_price_chart.py"
DEFAULT_ARGS = ["SP500", "GOLD", "SILVER", "6mo"]


def _collect_args(argv: list[str]) -> list[str]:
    env_args = os.environ.get("HERMES_COMMAND_ARGS", "")
    if env_args.strip():
        try:
            args = shlex.split(env_args)
        except ValueError:
            args = env_args.split()
    else:
        args = list(argv)
    expanded: list[str] = []
    for arg in args:
        try:
            parts = shlex.split(arg)
        except ValueError:
            parts = arg.split()
        expanded.extend(parts or [arg])
    return [a.strip() for a in expanded if a.strip()]


def main() -> int:
    args = _collect_args(sys.argv[1:]) or DEFAULT_ARGS
    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "spaghetti", *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        print("Spaghetti chart timed out")
        return 0
    except Exception as exc:
        print(f"Spaghetti chart failed: {exc}")
        return 0

    raw = (proc.stdout or proc.stderr or "").strip()
    if not raw:
        print("Spaghetti chart returned no output")
        return 0
    json_line = raw.splitlines()[-1]
    try:
        payload = json.loads(json_line)
    except json.JSONDecodeError:
        print(raw.splitlines()[-1][:500])
        return 0
    if payload.get("error"):
        print(f"Spaghetti: {payload.get('error')}")
        details = payload.get("details")
        if details:
            print(f"details: {details}")
        return 0
    text = payload.get("text_plain") or payload.get("text") or "Spaghetti chart ready"
    print(text)
    series = payload.get("series") or []
    if series:
        verify_bits = [f"{item.get('symbol')}={item.get('source')}:{item.get('token_id')}" for item in series]
        print(f"verify: duration={payload.get('duration')} " + " · ".join(verify_bits))
    chart_path = payload.get("chart_path")
    if chart_path and Path(str(chart_path)).is_file():
        print(f"MEDIA:{chart_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
