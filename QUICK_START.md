# Quick Start Guide

## Installation

```bash
# Install via ClawdHub (recommended)
clawdhub install evgyur/crypto-price

# Or clone manually
cd ~/.clawdbot/workspace/skills
git clone https://github.com/evgyur/crypto-price.git
pip install -r crypto-price/requirements.txt
```

## Usage Examples

### Get Bitcoin price and 24h chart
```bash
python3 scripts/get_price_chart.py BTC
```

### Get Ethereum price and 12h chart
```bash
python3 scripts/get_price_chart.py ETH 12h
```

### Get HYPE token price and 3h chart
```bash
python3 scripts/get_price_chart.py HYPE 3h
```

## Output

The script returns JSON with price data and chart path:

```json
{
  "symbol": "BTC",
  "price": 89946.00,
  "change_period_percent": -0.06,
  "chart_path": "/tmp/crypto_chart_BTC_1769142011.png",
  "text_plain": "BTC: $89946.00 USD (-0.06% over 24h)"
}
```

## Supported Timeframes

- `30m` - 30 minutes
- `3h` - 3 hours  
- `12h` - 12 hours
- `24h` - 24 hours (default)
- `2d` - 2 days

## Troubleshooting

**Script not found?**
- Ensure skill is installed in your Clawdbot workspace
- Check path: `~/.clawdbot/workspace/skills/crypto-price/`

**Missing matplotlib?**
```bash
pip install matplotlib
```

**API errors?**
- Check internet connection
- CoinGecko API is free but has rate limits
- Hyperliquid API may be temporarily unavailable
