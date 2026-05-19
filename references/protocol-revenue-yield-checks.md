# Protocol revenue / stablecoin yield claim checks

Use when verifying crypto post claims like `+25% annual revenue`, reserve-yield share, stablecoin supply, protocol revenue run-rate, or token fundamental impact.

## Pattern

1. Do web/social search first for the deal terms and language.
   - Use Perplexity/bird for announcement context.
   - Treat search summaries as leads, not final arithmetic.

2. Verify the numeric base with direct data APIs when possible.
   - Hyperliquid protocol revenue: DefiLlama fees API.
   - Stablecoin supply on a chain/protocol: DefiLlama stablecoins API.

3. Recalculate the claim explicitly.
   - `additional_revenue = stablecoin_supply * reserve_yield * protocol_share`
   - `annualized_revenue = last_30d_protocol_revenue * 365 / 30`
   - `uplift_pct = additional_revenue / annualized_revenue`

4. Present as a range, not a fake-precise number.
   - Reserve yields move with rates.
   - Stablecoin supply moves.
   - Revenue run-rate moves.
   - If the team did not publish guidance, call it a back-of-envelope estimate.

## Example: Hyperliquid USDC reserve-yield uplift

Useful direct calls:

```bash
python3 - <<'PY'
import requests

rev = requests.get(
    'https://api.llama.fi/summary/fees/hyperliquid?dataType=dailyRevenue',
    timeout=30,
).json()
print('30d revenue', rev.get('total30d'))
print('annualized 30d', rev.get('total30d') * 365 / 30)

stables = requests.get(
    'https://stablecoins.llama.fi/stablecoins',
    params={'chain': 'Hyperliquid L1'},
    timeout=30,
).json()
for asset in stables['peggedAssets']:
    if asset.get('symbol') == 'USDC':
        usdc = asset['chainCirculating']['Hyperliquid L1']['current']['peggedUSD']
        print('USDC on Hyperliquid L1', usdc)
        for y in [0.0325, 0.035, 0.0375]:
            add = usdc * y * 0.90
            print(y, 'additional', add, 'uplift_pct', add / (rev.get('total30d') * 365 / 30))
PY
```

Session-calibrated output shape:

```text
25% сходится, но формулировку лучше поправить: это не “платежи Circle”, а reserve-yield share по USDC в связке Coinbase/Circle.

$5.19B USDC × 3.25–3.75% yield × 90% share = ~$152–175M/year.
Hyperliquid protocol revenue: ~$51.4M за 30 дней = ~$625M annualized.
$152–175M / $625M = 24–28%.

Это back-of-envelope, не guidance команды.
```

## Pitfalls

- Do not cite `+25% revenue` as confirmed team guidance unless an official source says so.
- Do not write `Circle payments` if the mechanism is reserve-yield sharing via Coinbase/Circle.
- Do not trust a web-search answer when it supplies exact revenue math without direct API verification.
- Avoid markdown tables in Telegram replies; use labeled lines or compact bullets.
