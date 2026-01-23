#!/usr/bin/env python3
import json
import math
import re
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

DEFAULT_HOURS = 24
CANDLE_MINUTES = 15
CACHE_TTL_SEC = 300
COINGECKO_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price?ids={id}&vs_currencies={currency}"
COINGECKO_OHLC_URL = "https://api.coingecko.com/api/v3/coins/{id}/ohlc?vs_currency={currency}&days=1"
COINGECKO_SEARCH_URL = "https://api.coingecko.com/api/v3/search?query={query}"
COINGECKO_MARKET_CHART_URL = "https://api.coingecko.com/api/v3/coins/{id}/market_chart?vs_currency={currency}&days=1"
COINGECKO_MARKET_CHART_DAYS_URL = "https://api.coingecko.com/api/v3/coins/{id}/market_chart?vs_currency={currency}&days={days}"
HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"

TOKEN_ID_MAP = {
    "HYPE": "hyperliquid",
    "HYPERLIQUID": "hyperliquid",
}


def _json_error(message, details=None):
    payload = {"error": message}
    if details:
        payload["details"] = details
    print(json.dumps(payload))
    return 0


def _cache_path(prefix, token_id):
    safe = token_id.replace("/", "-")
    return f"/tmp/crypto_price_{prefix}_{safe}.json"


def _read_cache(path, max_age_sec):
    try:
        stat = os.stat(path)
    except FileNotFoundError:
        return None
    age = time.time() - stat.st_mtime
    if age > max_age_sec:
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def _write_cache(path, payload):
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
    except OSError:
        return


def _fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "clawdbot-crypto-price/1.0"},
    )
    retry_codes = {429, 502, 503, 504}
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                raise RuntimeError("invalid JSON") from exc
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in retry_codes and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            raise RuntimeError(str(exc)) from exc
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            raise RuntimeError(str(exc)) from exc
    raise RuntimeError(str(last_error))


def _post_json(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "clawdbot-crypto-price/1.0"},
    )
    retry_codes = {429, 502, 503, 504}
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                raise RuntimeError("invalid JSON") from exc
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in retry_codes and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            raise RuntimeError(str(exc)) from exc
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            raise RuntimeError(str(exc)) from exc
    raise RuntimeError(str(last_error))


def _post_json(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "clawdbot-crypto-price/1.0"},
    )
    retry_codes = {429, 502, 503, 504}
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                raise RuntimeError("invalid JSON") from exc
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in retry_codes and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            raise RuntimeError(str(exc)) from exc
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            raise RuntimeError(str(exc)) from exc
    raise RuntimeError(str(last_error))


def _get_price(token_id, currency):
    cache_path = _cache_path(f"price_{currency}", token_id)
    cached = _read_cache(cache_path, CACHE_TTL_SEC)
    if cached is not None:
        return cached
    data = _fetch_json(COINGECKO_PRICE_URL.format(id=token_id, currency=currency))
    _write_cache(cache_path, data)
    return data


def _get_ohlc(token_id, currency):
    cache_path = _cache_path(f"ohlc_{currency}", token_id)
    cached = _read_cache(cache_path, CACHE_TTL_SEC)
    if cached is not None:
        return cached
    data = _fetch_json(COINGECKO_OHLC_URL.format(id=token_id, currency=currency))
    _write_cache(cache_path, data)
    return data


def _get_market_chart(token_id, currency, days):
    cache_path = _cache_path(f"market_{currency}_{days}", token_id)
    cached = _read_cache(cache_path, CACHE_TTL_SEC)
    if cached is not None:
        return cached
    if days == 1:
        url = COINGECKO_MARKET_CHART_URL.format(id=token_id, currency=currency)
    else:
        url = COINGECKO_MARKET_CHART_DAYS_URL.format(id=token_id, currency=currency, days=days)
    data = _fetch_json(url)
    _write_cache(cache_path, data)
    return data


def _get_hyperliquid_meta():
    cache_path = _cache_path("hyperliquid_meta", "meta")
    cached = _read_cache(cache_path, CACHE_TTL_SEC)
    if cached is not None:
        return cached
    data = _post_json(HYPERLIQUID_INFO_URL, {"type": "metaAndAssetCtxs"})
    _write_cache(cache_path, data)
    return data


def _hyperliquid_lookup(symbol):
    try:
        meta, ctxs = _get_hyperliquid_meta()
    except RuntimeError:
        return None, None
    universe = meta.get("universe", [])
    mapping = {}
    for idx, entry in enumerate(universe):
        name = str(entry.get("name", "")).upper()
        if name:
            mapping[name] = idx
    idx = mapping.get(symbol.upper())
    if idx is None or idx >= len(ctxs):
        return None, None
    return universe[idx], ctxs[idx]


def _pick_hyperliquid_interval_minutes(total_minutes):
    if total_minutes <= 180:
        return 1
    if total_minutes <= 360:
        return 3
    if total_minutes <= 720:
        return 5
    if total_minutes <= 1440:
        return 15
    if total_minutes <= 4320:
        return 30
    if total_minutes <= 10080:
        return 60
    if total_minutes <= 20160:
        return 120
    if total_minutes <= 40320:
        return 240
    if total_minutes <= 80640:
        return 480
    return 1440


def _interval_minutes_to_str(minutes):
    if minutes < 60:
        return f"{int(minutes)}m"
    hours = int(minutes / 60)
    if hours < 24:
        return f"{hours}h"
    days = int(hours / 24)
    return f"{days}d"


def _get_hyperliquid_candles(symbol, total_minutes, interval_minutes):
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - int(total_minutes * 60 * 1000)
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": symbol.upper(),
            "interval": _interval_minutes_to_str(interval_minutes),
            "startTime": start_ms,
            "endTime": now_ms,
        },
    }
    data = _post_json(HYPERLIQUID_INFO_URL, payload)
    candles = []
    for row in data:
        try:
            ts_ms = int(row["t"])
            open_price = float(row["o"])
            high_price = float(row["h"])
            low_price = float(row["l"])
            close_price = float(row["c"])
        except (KeyError, TypeError, ValueError):
            continue
        candles.append((ts_ms, open_price, high_price, low_price, close_price))
    return candles


def _get_hyperliquid_meta():
    cache_path = _cache_path("hyperliquid_meta", "meta")
    cached = _read_cache(cache_path, CACHE_TTL_SEC)
    if cached is not None:
        return cached
    data = _post_json(HYPERLIQUID_INFO_URL, {"type": "metaAndAssetCtxs"})
    _write_cache(cache_path, data)
    return data


def _hyperliquid_lookup(symbol):
    try:
        meta, ctxs = _get_hyperliquid_meta()
    except RuntimeError:
        return None, None
    universe = meta.get("universe", [])
    mapping = {}
    for idx, entry in enumerate(universe):
        name = str(entry.get("name", "")).upper()
        if name:
            mapping[name] = idx
    idx = mapping.get(symbol.upper())
    if idx is None or idx >= len(ctxs):
        return None, None
    return universe[idx], ctxs[idx]


def _pick_hyperliquid_interval_minutes(total_minutes):
    if total_minutes <= 180:
        return 1
    if total_minutes <= 360:
        return 3
    if total_minutes <= 720:
        return 5
    if total_minutes <= 1440:
        return 15
    if total_minutes <= 4320:
        return 30
    if total_minutes <= 10080:
        return 60
    if total_minutes <= 20160:
        return 120
    if total_minutes <= 40320:
        return 240
    if total_minutes <= 80640:
        return 480
    return 1440


def _interval_minutes_to_str(minutes):
    if minutes < 60:
        return f"{int(minutes)}m"
    hours = int(minutes / 60)
    if hours < 24:
        return f"{hours}h"
    days = int(hours / 24)
    return f"{days}d"


def _get_hyperliquid_candles(symbol, total_minutes, interval_minutes):
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - int(total_minutes * 60 * 1000)
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": symbol.upper(),
            "interval": _interval_minutes_to_str(interval_minutes),
            "startTime": start_ms,
            "endTime": now_ms,
        },
    }
    data = _post_json(HYPERLIQUID_INFO_URL, payload)
    candles = []
    for row in data:
        try:
            ts_ms = int(row["t"])
            open_price = float(row["o"])
            high_price = float(row["h"])
            low_price = float(row["l"])
            close_price = float(row["c"])
        except (KeyError, TypeError, ValueError):
            continue
        candles.append((ts_ms, open_price, high_price, low_price, close_price))
    return candles


def _search_token_id(symbol):
    cache_path = _cache_path("search", symbol.upper())
    cached = _read_cache(cache_path, CACHE_TTL_SEC)
    if cached is None:
        data = _fetch_json(COINGECKO_SEARCH_URL.format(query=urllib.parse.quote(symbol)))
        _write_cache(cache_path, data)
    else:
        data = cached

    coins = data.get("coins", [])
    symbol_upper = symbol.upper()
    matches = [coin for coin in coins if coin.get("symbol", "").upper() == symbol_upper]
    if not matches:
        return None

    def _rank_key(coin):
        rank = coin.get("market_cap_rank")
        return rank if isinstance(rank, int) else 10**9

    matches.sort(key=_rank_key)
    return matches[0].get("id")


def _format_price(value):
    if value is None:
        return "n/a"
    if value >= 1:
        return f"{value:.2f}"
    return f"{value:.6f}"


def _build_candles_from_prices(price_points, hours, candle_minutes):
    if not price_points:
        return []
    price_points.sort(key=lambda row: row[0])
    last_ts = price_points[-1][0]
    start_ts = last_ts - (hours * 3600 * 1000)
    bucket_ms = candle_minutes * 60 * 1000
    candles = []
    bucket = None
    for ts, price in price_points:
        if ts < start_ts:
            continue
        bucket_start = (int(ts) // bucket_ms) * bucket_ms
        if bucket is None or bucket["bucket_start"] != bucket_start:
            if bucket is not None:
                candles.append((
                    bucket["bucket_start"],
                    bucket["open"],
                    bucket["high"],
                    bucket["low"],
                    bucket["close"],
                ))
            bucket = {
                "bucket_start": bucket_start,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
            }
        else:
            bucket["high"] = max(bucket["high"], price)
            bucket["low"] = min(bucket["low"], price)
            bucket["close"] = price
    if bucket is not None:
        candles.append((
            bucket["bucket_start"],
            bucket["open"],
            bucket["high"],
            bucket["low"],
            bucket["close"],
        ))
    return candles


def _parse_duration(args):
    for arg in args:
        cleaned = arg.strip().lower()
        match = re.match(r"^(\d+(?:\.\d+)?)([mhd])?$", cleaned)
        if not match:
            continue
        value = float(match.group(1))
        unit = match.group(2) or "h"
        if unit == "m":
            total_minutes = max(1.0, value)
            label = f"{int(value)}m" if value.is_integer() else f"{value}m"
        elif unit == "d":
            total_minutes = max(1.0, value * 24 * 60)
            label = f"{int(value)}d" if value.is_integer() else f"{value}d"
        else:
            total_minutes = max(1.0, value * 60)
            label = f"{int(value)}h" if value.is_integer() else f"{value}h"
        return total_minutes, label
    return float(DEFAULT_HOURS * 60), f"{DEFAULT_HOURS}h"


def _pick_candle_minutes(total_minutes):
    if total_minutes <= 360:
        return 5
    if total_minutes <= 1440:
        return 15
    if total_minutes <= 4320:
        return 30
    return 60


def _timestamp_to_datetime(ts_value):
    ts = float(ts_value)
    if ts >= 1e12:
        ts = ts / 1000.0
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _build_chart(symbol, ohlc_rows, currency, label):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.lines import Line2D
        from matplotlib.patches import Rectangle
    except Exception:
        return None

    if not ohlc_rows:
        return None

    fig, ax = plt.subplots(figsize=(8, 8), facecolor="#0f141c")
    ax.set_facecolor("#0f141c")

    times = [_timestamp_to_datetime(row[0]) for row in ohlc_rows]
    x_vals = mdates.date2num(times)
    widths = []
    if len(x_vals) > 1:
        delta = min(x_vals[i + 1] - x_vals[i] for i in range(len(x_vals) - 1))
        widths = [delta * 0.7] * len(x_vals)
    else:
        widths = [0.02] * len(x_vals)

    lows = []
    highs = []
    for idx, row in enumerate(ohlc_rows):
        _ts, open_price, high_price, low_price, close_price = row
        color = "#26a69a" if close_price >= open_price else "#ef5350"
        x = x_vals[idx]
        width = widths[idx]
        ax.add_line(Line2D([x, x], [low_price, high_price], color=color, linewidth=1.0))
        lower = min(open_price, close_price)
        height = max(abs(close_price - open_price), 1e-9)
        rect = Rectangle((x - width / 2, lower), width, height, facecolor=color, edgecolor=color)
        ax.add_patch(rect)
        lows.append(low_price)
        highs.append(high_price)

    ax.set_title(f"{symbol} last {label}", loc="left", fontsize=11, color="#e6edf3", pad=10)
    ax.set_xlabel("Time (UTC)", color="#8b949e")
    ax.set_ylabel(currency.upper(), color="#8b949e")

    ax.tick_params(axis="x", colors="#8b949e")
    ax.tick_params(axis="y", colors="#8b949e")
    for spine in ax.spines.values():
        spine.set_color("#2a2f38")

    ax.grid(True, linestyle="-", linewidth=0.6, color="#1f2630", alpha=0.8)

    if len(x_vals) > 1:
        ax.set_xlim(min(x_vals) - delta, max(x_vals) + delta)
    if lows and highs:
        min_y = min(lows)
        max_y = max(highs)
        pad = (max_y - min_y) * 0.05 if max_y > min_y else max_y * 0.01
        ax.set_ylim(min_y - pad, max_y + pad)

    locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.tick_params(axis="x", labelrotation=0)

    ts = int(time.time())
    chart_path = f"/tmp/crypto_chart_{symbol}_{ts}.png"
    fig.tight_layout()
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    return chart_path


def main():
    if len(sys.argv) < 2:
        return _json_error("missing symbol", "Usage: get_price_chart.py <symbol>")

    raw_symbol = sys.argv[1].strip()
    if not raw_symbol:
        return _json_error("missing symbol", "Usage: get_price_chart.py <symbol>")

    symbol_upper = raw_symbol.upper()
    token_id = TOKEN_ID_MAP.get(symbol_upper)
    if token_id is None:
        token_id = raw_symbol.lower()

    total_minutes, label = _parse_duration(sys.argv[2:])
    hours = total_minutes / 60.0
    source = "coingecko"
    currency = "usdt"
    price_usdt = None
    hl_meta, hl_ctx = _hyperliquid_lookup(symbol_upper)
    if hl_ctx:
        source = "hyperliquid"
        currency = "usd"
        try:
            price_usdt = float(hl_ctx.get("markPx") or hl_ctx.get("midPx"))
        except (TypeError, ValueError):
            price_usdt = None
    if price_usdt is None:
        try:
            price_payload = _get_price(token_id, currency)
        except RuntimeError as exc:
            return _json_error("price lookup failed", str(exc))

        price_entry = price_payload.get(token_id, {})
        price_usdt = price_entry.get(currency)
        if price_usdt is None:
            currency = "usd"
            try:
                price_payload = _get_price(token_id, currency)
            except RuntimeError as exc:
                return _json_error("price lookup failed", str(exc))
            price_entry = price_payload.get(token_id, {})
            price_usdt = price_entry.get(currency)

        if price_usdt is None and token_id == raw_symbol.lower():
            try:
                searched_id = _search_token_id(symbol_upper)
            except RuntimeError as exc:
                return _json_error("token search failed", str(exc))
            if searched_id:
                token_id = searched_id
                currency = "usdt"
                try:
                    price_payload = _get_price(token_id, currency)
                except RuntimeError as exc:
                    return _json_error("price lookup failed", str(exc))
                price_entry = price_payload.get(token_id, {})
                price_usdt = price_entry.get(currency)
                if price_usdt is None:
                    currency = "usd"
                    try:
                        price_payload = _get_price(token_id, currency)
                    except RuntimeError as exc:
                        return _json_error("price lookup failed", str(exc))
                    price_entry = price_payload.get(token_id, {})
                    price_usdt = price_entry.get(currency)

    if price_usdt is None:
        return _json_error("token not found", f"CoinGecko id: {token_id}")

    candles = []
    candle_minutes = _pick_candle_minutes(total_minutes)
    if source == "hyperliquid":
        interval_minutes = _pick_hyperliquid_interval_minutes(total_minutes)
        candle_minutes = interval_minutes
        try:
            candles = _get_hyperliquid_candles(symbol_upper, total_minutes, interval_minutes)
        except RuntimeError:
            candles = []

    if not candles:
        try:
            days = max(1, int(math.ceil(total_minutes / 1440.0)))
            if days > 365:
                days = 365
            chart_payload = _get_market_chart(token_id, currency, days)
            price_points = chart_payload.get("prices", [])
            candles = _build_candles_from_prices(price_points, hours, candle_minutes)
        except RuntimeError:
            candles = []

    if not candles:
        candle_minutes = 30
        try:
            ohlc_payload = _get_ohlc(token_id, currency)
        except RuntimeError:
            ohlc_payload = []
        for row in ohlc_payload:
            if len(row) < 5:
                continue
            ts_ms, open_price, high_price, low_price, close_price = row
            candles.append((ts_ms, open_price, high_price, low_price, close_price))

    candles.sort(key=lambda item: item[0])
    if candles:
        target = max(2, int((hours * 60) / candle_minutes))
        last_points = candles[-target:]
    else:
        last_points = []

    change_period = None
    change_period_percent = None
    price_period_ago = None

    if len(last_points) >= 2:
        price_period_ago = last_points[0][4]
        if price_period_ago:
            change_period = price_usdt - price_period_ago
            change_period_percent = (change_period / price_period_ago) * 100
    chart_path = _build_chart(symbol_upper, last_points, currency, label)

    if change_period_percent is None:
        change_text = f"{label} n/a"
    else:
        sign = "+" if change_period_percent >= 0 else ""
        change_text = f"{sign}{change_period_percent:.2f}% over {label}"

    text = f"{symbol_upper}: ${_format_price(price_usdt)} {currency.upper()} ({change_text})"
    text = text.replace("*", "")
    result = {
        "symbol": symbol_upper,
        "token_id": token_id,
        "source": source,
        "currency": currency.upper(),
        "hours": hours,
        "duration_label": label,
        "candle_minutes": candle_minutes,
        "price": price_usdt,
        "price_usdt": price_usdt,
        "change_12h": change_period,
        "change_12h_percent": change_period_percent,
        "change_period": change_period,
        "change_period_percent": change_period_percent,
        "chart_path": chart_path,
        "text": text,
        "text_plain": text,
    }
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
