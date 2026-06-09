# HIP-3 / TradeXYZ tickers on Hyperliquid

Use this reference when implementing or debugging `/price` source routing for non-crypto assets on Hyperliquid.

## Core rule

HIP-3 builder-deployed perpetuals do not appear as bare symbols in the default perp universe. They live under a perp dex and must be queried with a fully-qualified `dex:ticker` coin string.

Current observed dex:
- dex name: `xyz`
- full name: `XYZ` / TradeXYZ
- deployer: `0x88806a71d74ad0a510b350545c9ae490912f0888`
- query metadata: `POST /info {"type":"metaAndAssetCtxs","dex":"xyz"}`
- query mids: `POST /info {"type":"allMids","dex":"xyz"}`
- query candles: `POST /info {"type":"candleSnapshot","req":{"coin":"xyz:SILVER",...}}`

Do not use `SILVER` for candles; use `xyz:SILVER`.

## Important aliases for `/price`

- `SILVER`, `XAG`, `XAGUSD` → `xyz:SILVER` — silver / XAG proxy
- `GOLD`, `XAU`, `XAUUSD` → `xyz:GOLD` — gold / XAU proxy
- `SPX`, `SP500`, `SPY`, `S&P500` → `xyz:SP500` — S&P 500 perp
- `NASDAQ`, `NDX`, `NAS100`, `US100` → `xyz:XYZ100` — TradeXYZ 100, Nasdaq-100-like basket of 100 large non-financial US-listed companies
- `WTI`, `OIL`, `CRUDE` → `xyz:CL` — WTI crude oil proxy
- `BRENT` → `xyz:BRENTOIL` — Brent crude oil proxy
- `DXY` → `xyz:DXY` — US Dollar Index
- `NIKKEI`, `JP225` → `xyz:JP225` — Japan Nikkei 225 proxy
- `KOSPI`, `KR200` → `xyz:KR200` — Korea KOSPI 200 proxy
- `NIFTY` → `xyz:NIFTY` — India Nifty 50 proxy
- `IBOV`, `BOVESPA` → `xyz:IBOV` — Brazil Ibovespa proxy
- `JPY`, `EUR`, `GBP`, `KRW` → `xyz:<ticker>` — FX proxies against USD

## Current category map

Indices / macro:
- `xyz:XYZ100` — TradeXYZ 100 / Nasdaq-100-like equity basket
- `xyz:SP500` — S&P 500
- `xyz:JP225` — Nikkei 225
- `xyz:KR200` — KOSPI 200
- `xyz:NIFTY` — Nifty 50
- `xyz:IBOV` — Ibovespa
- `xyz:DXY` — US Dollar Index
- `xyz:VIX`, `xyz:VOL` — volatility synthetic/proxy markets

Commodities:
- `xyz:GOLD`, `xyz:SILVER`, `xyz:PLATINUM`, `xyz:PALLADIUM`
- `xyz:CL`, `xyz:BRENTOIL`, `xyz:NATGAS`, `xyz:TTF`
- `xyz:COPPER`, `xyz:ALUMINIUM`, `xyz:URANIUM`
- `xyz:CORN`, `xyz:WHEAT`

ETFs / regional/theme proxies:
- `xyz:EWJ`, `xyz:EWY`, `xyz:EWZ`, `xyz:EWT`
- `xyz:XLE`, `xyz:URNM`, `xyz:SPCX`

Single-stock equity perps observed:
- US mega/tech: `AAPL`, `MSFT`, `NVDA`, `TSLA`, `AMZN`, `GOOGL`, `META`, `AMD`, `AVGO`, `ORCL`, `NFLX`, `PLTR`, `COIN`, `MSTR`
- Semis/hardware: `INTC`, `MU`, `MRVL`, `ASML`, `TSM`, `ARM`, `DELL`, `IBM`, `WDC`, `SNDK`, `SKHX`, `KIOXIA`, `SMSN`, `H100`, `DRAM`
- Other equities: `HOOD`, `CRCL`, `COST`, `LLY`, `RIVN`, `BABA`, `USAR`, `CRWV`, `GME`, `SOFTBANK`, `HYUNDAI`, `HIMS`, `DKNG`, `LITE`, `BX`, `RKLB`, `BIRD`, `CBRS`, `ZM`, `EBAY`, `BB`, `QNT`, `NOW`, `NBIS`

Synthetic / needs UI verification before strong claims:
- `xyz:PURRDAT`
- `xyz:MINIMAX`

## Verification checklist

When adding a new alias or debugging `/price`:
1. `perpDexs` includes a dex object, not just `null` for the default dex.
2. `metaAndAssetCtxs` with `dex="xyz"` contains the full market name.
3. `allMids` with `dex="xyz"` returns a price for the same full name.
4. `candleSnapshot` succeeds with `coin="xyz:<TICKER>"`.
5. The output JSON has `source="hyperliquid"`, `token_id="xyz:<TICKER>"`, and a valid `chart_path`.
