---
name: crypto-price-ops-fallback
description: Handle API rate limits, source failures, and user-safe error output.
---

# ops-fallback

## Goal
Стабильно обработать ошибки API/сети/лимитов и вернуть понятный safe output.

## Steps
1. Классифицировать ошибку (429/timeout/invalid symbol/source unavailable).
2. Применить retry/cached fallback (если доступен).
3. Вернуть краткий error JSON без внутренних stack traces.

## Done Criteria
- ошибки детерминированы и понятны
- нет утечки внутренних трассировок
- есть actionable next step (retry, symbol check, duration adjust)
