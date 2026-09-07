# Nifty 500 Automated Streamlit Scanner

## Architecture

- `scanner.py` — scheduled scanner
- `app.py` — Streamlit mobile dashboard
- `.github/workflows/nifty500_scan.yml` — automatic 09:30 and 10:00 IST jobs
- `results/` — generated CSV results

## Important

The scanner uses Yahoo Finance for OHLCV. Yahoo Finance data is not a guaranteed exchange-grade real-time feed.

Futures OI, option-chain PCR and IV are not fabricated. They require a supported derivatives data source.

## GitHub setup

1. Create a GitHub repository.
2. Upload all files from this folder.
3. In Streamlit Community Cloud, deploy `app.py`.
4. Enable GitHub Actions.
5. The workflow runs on weekdays at approximately 09:30 and 10:00 IST using UTC cron.
6. The workflow commits updated CSV results to the repository.

## Schedule

09:30 IST = 04:00 UTC
10:00 IST = 04:30 UTC

Use weekday cron expressions:

`0 4 * * 1-5`
`30 4 * * 1-5`

Note: GitHub Actions scheduling can be delayed. It is not an exchange-grade scheduler.

## Mobile

Open the Streamlit public URL from any phone browser.

## Before production trading

Validate signals against NSE/authorized market data. This scanner is a rule-based technical research tool, not investment advice.
