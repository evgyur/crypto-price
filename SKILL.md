---
name: crypto-price
description: Router skill for crypto token price + candlestick chart generation via Hyperliquid/CoinGecko.
metadata:
  clawdbot:
    emoji: 📈
    command: /crypto-price
    requires:
      bins: ["python3"]
---

# /crypto-price

Router для скилла цен и графиков крипты.

## Trigger
Когда нужен токен прайс, изменение за период или график (`BTC`, `ETH`, `HYPE`, ...).

## Command
```bash
python3 {baseDir}/scripts/get_price_chart.py <SYMBOL> [duration]
```

Duration: формат `<число>[m|h|d]`, без суффикса = часы. Примеры: `30m`, `2h`, `3h`, `12h`, `24h`, `2d`. Default: `24h`.

## Router Map
- source/duration routing -> `modules/source-routing/SKILL.md`
- data fetch + chart artifact -> `modules/price-chart/SKILL.md`
- failures/rate-limit handling -> `modules/ops-fallback/SKILL.md`
- protocol revenue / stablecoin yield claim checks -> `references/protocol-revenue-yield-checks.md`

## Protocol revenue / yield claim verification

When the user asks to confirm crypto revenue claims (`+25% annual revenue`, reserve-yield share, token fundamental impact), do not stop at web-search summaries. Use direct data APIs where possible, then recalculate the claim explicitly:
- protocol revenue run-rate: DefiLlama fees API, usually last 30d annualized
- stablecoin supply: DefiLlama stablecoins API by chain/protocol
- uplift: `supply * reserve_yield * protocol_share / annualized_revenue`

Return ranges and label them as back-of-envelope unless the team published official guidance. For details and a Hyperliquid/Coinbase/Circle worked example, see `references/protocol-revenue-yield-checks.md`.

## Quick-command aliases

If a token-specific slash alias (for example `/hype`) uses Hermes `quick_commands` with `type: exec`, the alias config must forward duration arguments (`append_args: true`) or expose `HERMES_COMMAND_ARGS` to the wrapper. Otherwise `/alias 2h` can call this script without `2h` and return a default-period chart while looking superficially successful. See `hermes-agent` → `references/gateway-quick-commands.md` for the gateway mechanics.

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
- `MEDIA:` оставляй только как запасной вариант для web/local render, когда `message` tool не нужен.

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
- [ ] JSON содержит `price|change_period_percent|text_plain` при success
- [ ] `chart_path` (если есть) указывает на существующий `.png`
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

## Backward-Compat Map
- legacy запуск `python3 {baseDir}/scripts/get_price_chart.py <SYMBOL> [duration]` сохранён
- legacy описание перенесено в `references/legacy-SKILL.md`
- код скрипта оставлен без rename для совместимости
- JSON должен включать и `duration`, и `duration_label`; некоторые OpenClaw command aliases and chat delivery checks look for `duration` explicitly.
- `/hype` in OpenClaw should remain a thin alias skill that delegates to `crypto-price/scripts/get_price_chart.py HYPE [duration]`; do not duplicate pricing or charting logic in the alias.
