---
name: crypto-price
description: Router skill for crypto token price + candlestick chart generation via Hyperliquid/CoinGecko.
metadata:
  clawdbot:
    emoji: 📈
    command: /crypto-price
    aliases: [/hype]
    requires:
      bins: ["python3"]
---

# /crypto-price

Router для скилла цен и графиков крипты.

## Trigger
Когда нужен токен прайс, изменение за период или график (`BTC`, `ETH`, `HYPE`, ...).

## Commands

### `/crypto-price <SYMBOL> [duration]`
Canonical generic command for any supported token/asset.

```bash
python3 {baseDir}/scripts/get_price_chart.py <SYMBOL> [duration]
```

Source routing is Hyperliquid-first for all live perp symbols from `metaAndAssetCtxs`, then CoinGecko for crypto tokens, then Yahoo Finance for traditional tickers/aliases (`SILVER`→`SI=F`, `GOLD`→`GC=F`, `SPX`→`^GSPC`, FX, stocks/ETFs when a Yahoo ticker is supplied).

### `/price <SYMBOL> [duration]`
Quick command wrapper for Telegram/gateway. Prints text + verify + `MEDIA:<png>`.

```bash
python3 {baseDir}/scripts/price_quick.py <SYMBOL> [duration]
```

### `/spaghetti <SYMBOL...> [duration]`
Multi-asset normalized line chart. Use for comparing assets over the same period, e.g. SP500 vs GOLD vs SILVER for 6 months. It normalizes every series to 0% at the first candle and plots % change, so different units/prices are comparable.

```bash
python3 {baseDir}/scripts/get_price_chart.py spaghetti SP500 GOLD SILVER 6mo
python3 {baseDir}/scripts/spaghetti_quick.py SP500 GOLD SILVER 6mo
```

Aliases: `compare`, `multi`, `basket` are accepted as the first script command. Use comma input too: `SP500,GOLD,SILVER 6mo`.

### `/hype [duration]`
Built-in alias command owned by this same skill. It must remain inside `crypto-price`, not a separate `hype` skill.

```bash
python3 {baseDir}/scripts/hype_quick.py [duration]
```

The alias delegates to:

```bash
python3 {baseDir}/scripts/get_price_chart.py HYPE [duration]
```

## Command contract

Duration: минуты/часы/дни/недели/месяцы. Компактный формат `<число>[m|h|d|w|mo]`, без суффикса = часы. Примеры: `30m`, `2h`, `3h`, `12h`, `24h`, `2d`, `1w`, `2weeks`, `1mo`, `2months`; также поддерживаются раздельные формы вроде `1 week`, `2 months`, `30 мин`, `3 часа`, `1 месяц`. Месяц считается как 30 дней. Default: `24h`.

## Router Map
- source/duration routing -> `modules/source-routing/SKILL.md`
- data fetch + chart artifact -> `modules/price-chart/SKILL.md`
- failures/rate-limit handling -> `modules/ops-fallback/SKILL.md`
- Hyperliquid live symbol snapshot -> `references/hyperliquid-symbol-map.md`
- HIP-3 / TradeXYZ ticker meanings -> `references/hip3-tradexyz-tickers.md`
- protocol revenue / stablecoin yield claim checks -> `references/protocol-revenue-yield-checks.md`

## HIP-3 routing pitfall

Do not conclude that a non-crypto asset is absent from Hyperliquid after checking only the default perp universe (`metaAndAssetCtxs`) and spot universe (`spotMetaAndAssetCtxs`). HIP-3 builder-deployed markets live under perp dex names and use fully-qualified symbols like `xyz:SILVER`.

Correct lookup order for `/price <symbol>`:
1. Check default Hyperliquid perps.
2. Query `perpDexs` to discover HIP-3 dexes.
3. For each dex, query `metaAndAssetCtxs` with `dex=<name>` and match the market name or alias.
4. Query candles with the full `dex:ticker` coin string, e.g. `xyz:SILVER`, not bare `SILVER`.
5. Only then fall back to CoinGecko/Yahoo.

Alias examples from TradeXYZ/HIP-3: `SILVER`→`xyz:SILVER`, `GOLD`→`xyz:GOLD`, `SPX`/`SP500`→`xyz:SP500`, `NASDAQ`/`NDX`→`xyz:XYZ100`, `WTI`→`xyz:CL`, `BRENT`→`xyz:BRENTOIL`. See `references/hip3-tradexyz-tickers.md` before changing source routing.

## Protocol revenue / yield claim verification

When the user asks to confirm crypto revenue claims (`+25% annual revenue`, reserve-yield share, token fundamental impact), do not stop at web-search summaries. Use direct data APIs where possible, then recalculate the claim explicitly:
- protocol revenue run-rate: DefiLlama fees API, usually last 30d annualized
- stablecoin supply: DefiLlama stablecoins API by chain/protocol
- uplift: `supply * reserve_yield * protocol_share / annualized_revenue`

Return ranges and label them as back-of-envelope unless the team published official guidance. For details and a Hyperliquid/Coinbase/Circle worked example, see `references/protocol-revenue-yield-checks.md`.

## Quick-command aliases

If a token-specific slash alias (for example `/hype`) uses Hermes `quick_commands` with `type: exec`, keep the alias inside this `crypto-price` skill and point the quick command to this skill's wrapper (`scripts/hype_quick.py`). The alias config must forward duration arguments (`append_args: true`) or expose `HERMES_COMMAND_ARGS` to the wrapper. Otherwise `/alias 2h` can call this script without `2h` and return a default-period chart while looking superficially successful. See `hermes-agent` → `references/gateway-quick-commands.md` for the gateway mechanics.

## Output Contract (обязательный)
Всегда вернуть:
1) `symbol` и `duration`
2) `price` и `change_period_percent` (или error)
3) `chart_path` (если есть)
4) `text_plain` без лишнего форматирования
5) краткий verify (по JSON/файлу)

Если `chart_path` присутствует, нужно приложить PNG вместе с `text_plain`.

### Delivery Rule (важно)
- В Telegram и других чат-каналах с вложениями отправляй график через `message` tool как файл (`filePath`/`path` = `chart_path`).
- После `message action=send` отвечай только `NO_REPLY`, чтобы не было дубля.
- Не полагайся на `MEDIA:` для файлов из `/tmp` в Telegram, это может не прикрепиться.
- Если доступный Telegram sender поддерживает только текст с `MEDIA:<path>` (например `send_message` без отдельного `filePath`), сначала скопируй PNG из `/tmp` в устойчивый путь вроде `/home/hermes/workspace/artifacts/crypto_chart_<SYMBOL>_<ts>.png`, проверь `test -s`/размер, затем отправь `MEDIA:<persistent_path>`. Если текст+media одним сообщением таймаутится, отправь сначала короткий caption/verify, затем отдельное media-сообщение, и всё равно финаль `NO_REPLY`.
- `MEDIA:` оставляй только как запасной вариант для web/local render, когда `message` tool не нужен.

### Duplicate-output triage
If user shows a duplicated caption (`HYPE...` + `verify...` repeated under one chart), do not start by rewriting the price script. First check layers:
1. Run `python3 scripts/get_price_chart.py HYPE <duration>` and confirm JSON contains one `text_plain`, one `verify`, and one `chart_path`.
2. If script output is not duplicated, cause is almost certainly delivery layer: caption + follow-up text, `MEDIA:` + final response, or missing `NO_REPLY` after `message` tool.
3. Verify the Telegram shape with an exact message fetch when possible. If message A has `has_media=true`/photo and the price text as caption, and message B has `has_media=false` with the same text, this is OpenClaw delivery dedupe treating `text+media` and final `text-only` as different payloads.
4. For OpenClaw, inspect `reply-delivery.ts`, `agent-runner-payloads.ts`, and `block-reply-pipeline.ts`; the durable fix is to suppress a later text-only final payload when the same text was already delivered as a media caption. See `references/openclaw-media-caption-dedupe.md`.
5. Check transcript/session JSONL: if toolResult is single but Telegram send/assistant response is double — fix gateway/skill delivery instructions, not price calculation.
6. For live Claw additionally check logs around user message: memory-compaction/tool allowlist failures can surface as duplicate diagnostic replies but are a separate gateway/tool-policy issue.

## Setup / dependency check
- Chart rendering imports `matplotlib` inside `_build_chart`. If JSON returns `chart_path: null` while candles exist, first verify the Python environment used by the gateway/quick command:
  ```bash
  /opt/hermes-agent/venv/bin/python3 - <<'PY'
  import matplotlib
  print(matplotlib.__version__)
  PY
  ```
- If missing in that venv, install it there and rerun the script:
  ```bash
  /opt/hermes-agent/venv/bin/python3 -m pip install matplotlib
  /opt/hermes-agent/venv/bin/python3 /home/hermes/.hermes/skills/crypto-price/scripts/get_price_chart.py HYPE 24h
  ```
- Capture the durable lesson as “install the chart dependency in the same Python env the gateway uses”, not as a claim that charting is broken.

## Quick Test Checklist
- [ ] `/opt/hermes-agent/venv/bin/python3 /home/hermes/.hermes/skills/crypto-price/scripts/get_price_chart.py BTC`
- [ ] `python3 /home/hermes/.hermes/skills/crypto-price/scripts/get_price_chart.py HYPE 12h`
- [ ] `python3 /home/hermes/.hermes/skills/crypto-price/scripts/get_price_chart.py HYPE 2h` returns `duration: "2h"`, `text_plain` says `over 2h`, and `chart_path` points to an existing PNG.
- [ ] `python3 /home/hermes/.hermes/skills/crypto-price/scripts/get_price_chart.py HYPE 1w` returns `duration: "1w"` and a week-scale chart.
- [ ] `python3 /home/hermes/.hermes/skills/crypto-price/scripts/get_price_chart.py HYPE 1mo` returns `duration: "1mo"` and a month-scale chart.
- [ ] `HERMES_COMMAND_ARGS='1 week' /opt/hermes-agent/venv/bin/python3 /home/hermes/.hermes/skills/crypto-price/scripts/hype_quick.py` prints `over 1w` and `MEDIA:<png>`.
- [ ] JSON содержит `price|change_period_percent|text_plain` при success
- [ ] For short windows like `2h`, visually verify the chart spans the requested duration, not a trimmed subset. The chart builder must not cut the requested candle window for “breathing room”; use the full duration for both change calculation and x-axis.
- [ ] If a fractal lands on the same candle as the absolute high/low, verify the chart shows only one price label for that point; absolute markers own those labels to avoid doubled text.
- [ ] invalid symbol возвращает понятный error JSON

## Manual Review Checklist
- [ ] нет секретов/токенов/chat id в skill-файлах
- [ ] `text_plain` используется как есть (без дополнительной разметки)
- [ ] fallback path не раскрывает внутренние stack traces
- [ ] команда backward-compatible с legacy usage

## Done Criteria
- [ ] `SKILL.md` has valid frontmatter and command contract.
- [ ] `scripts/get_price_chart.py HYPE 12h` returns JSON with `symbol`, `duration`, `price`, `change_period_percent`, `text_plain`, and optional `chart_path`.
- [ ] If `chart_path` is returned, the PNG exists and can be attached by the chat channel.
- [ ] Invalid symbols return structured error JSON without stack traces.

## Canonical Repo / Push Notes
- Runtime installs under `~/.hermes/skills/crypto-price` may not be git worktrees. The canonical public repo is `https://github.com/evgyur/crypto-price.git`.
- When pushing runtime fixes, clone/sync into a clean temp checkout of that repo; preserve repo metadata like `.github/workflows`, docs, `.clawdhub`, fonts, and publish files.
- Prefer a surgical patch in the clean checkout over copying the whole runtime file; runtime files may contain whitespace/local drift that would pollute the canonical diff.
- Push the default remote branch (`origin/HEAD`; currently `master`) unless the user asks for another branch.
- After push, verify `git ls-remote`/remote-head match and, if GitHub Actions are configured, poll the latest workflow run until `success` or report the failure explicitly.

## Backward-Compat Map
- legacy запуск `python3 {baseDir}/scripts/get_price_chart.py <SYMBOL> [duration]` сохранён
- legacy описание перенесено в `references/legacy-SKILL.md`
- код скрипта оставлен без rename для совместимости
- JSON должен включать и `duration`, и `duration_label`; некоторые OpenClaw command aliases and chat delivery checks look for `duration` explicitly.
- `scripts/price_quick.py`: generic `/price <SYMBOL> [duration]` wrapper; parses argv and `HERMES_COMMAND_ARGS`, prints `text_plain`, verify line, and `MEDIA:<png>`.
- `scripts/spaghetti_quick.py`: `/spaghetti <SYMBOL...> [duration]` wrapper for normalized multi-asset comparison charts; default is `SP500 GOLD SILVER 6mo`.
- `/hype` in OpenClaw/Hermes must remain a thin alias command inside this same `crypto-price` skill that delegates to `crypto-price/scripts/get_price_chart.py HYPE [duration]`; do not create or maintain a separate `hype` skill.
- Period aliases must preserve the full requested window end-to-end. A prior bug accepted `2h` and captioned `over 2h`, but then trimmed candles to 80% for chart “breathing room”, so the chart/change used ~96 minutes. Do not trim requested-duration candles; if visual padding is needed, adjust axis margins only, not data selection.
