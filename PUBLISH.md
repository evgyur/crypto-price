# Publishing to GitHub and ClawdHub

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `crypto-price`
3. Description: `📈 Clawdbot skill for cryptocurrency price lookup and candlestick chart generation`
4. Visibility: Public
5. **Do NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 2: Push to GitHub

```bash
cd /home/eyurc/clawd/skills/crypto-price

# Add remote
git remote add origin git@github.com:evgyur/crypto-price.git

# Commit all files
git add -A
git commit -m "Initial commit: Crypto Price & Chart skill for Clawdbot"

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Publish to ClawdHub

ClawdHub automatically discovers skills from GitHub repositories. To publish:

1. **Ensure your repository is public** on GitHub
2. **Repository structure** should match:
   ```
   crypto-price/
   ├── SKILL.md          # Required
   ├── README.md         # Recommended
   ├── scripts/
   │   └── get_price_chart.py
   └── requirements.txt  # Optional
   ```

3. **Wait for auto-discovery** or manually submit:
   - Visit https://clawdhub.com
   - Look for "Submit Skill" or contact ClawdHub maintainers
   - Provide your GitHub repo URL: `https://github.com/evgyur/crypto-price`

4. **Verify on ClawdHub**:
   - Once published, your skill will be available at:
   - `https://clawdhub.com/evgyur/crypto-price`
   - Users can install with: `clawdhub install evgyur/crypto-price`

## Repository Structure

```
crypto-price/
├── .clawdhub/
│   └── origin.json          # ClawdHub metadata
├── scripts/
│   └── get_price_chart.py   # Main script
├── .gitignore               # Git ignore rules
├── README.md                # GitHub README
├── requirements.txt         # Python dependencies
└── SKILL.md                 # Clawdbot skill definition
```

## Tags and Releases

For versioning, create GitHub releases:

```bash
git tag -a v1.0.0 -m "Initial release: Crypto Price & Chart skill"
git push origin v1.0.0
```

## Verification

After publishing, verify installation:

```bash
# Install from ClawdHub
clawdhub install evgyur/crypto-price

# Check skill
clawdbot skills info crypto-price

# Test script
python3 ~/.clawdbot/workspace/skills/crypto-price/scripts/get_price_chart.py BTC
```
