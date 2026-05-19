---
name: crypto-price-price-chart
description: Fetch current price + period delta + candlestick chart artifact.
---

# price-chart

## Goal
Вернуть цену, % изменения за период и путь к PNG графику.

## Steps
1. Запустить `scripts/get_price_chart.py <SYMBOL> [duration]`.
2. Проверить JSON: `price`, `change_period_percent`, `text_plain`.
3. Если есть `chart_path` — проверить, что PNG файл существует.

## Done Criteria
- JSON ответ валиден
- price и change_period_percent присутствуют
- chart_path (если есть) указывает на реальный файл
- для Telegram chart_path отправляется как вложение через `message` tool, не через `MEDIA:` из `/tmp`
