---
name: crypto-price-source-routing
description: Resolve token source path (Hyperliquid vs CoinGecko) and duration parsing.
---

# source-routing

## Goal
Корректно определить источник данных и диапазон для запроса цены/графика.

## Steps
1. Нормализовать symbol (`BTC`, `HYPE`, ...).
2. Распарсить duration (`30m|3h|2d`, default `24h`).
3. Выбрать source path:
   - Hyperliquid при доступности токена
   - CoinGecko fallback.

## Done Criteria
- symbol и duration валидны
- выбран один source path
- нет silent-fallback с неконсистентным результатом
