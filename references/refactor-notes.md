# crypto-price refactor notes

## references/*
- `legacy-SKILL.md` — исходный монолитный SKILL до router-рефактора.
- `refactor-notes.md` — карта текущих модулей.

## module split
- `source-routing` — выбор Hyperliquid/CoinGecko + parsing duration
- `price-chart` — основной execution path и проверка chart artifact
- `ops-fallback` — ошибки/лимиты/retry-safe output
