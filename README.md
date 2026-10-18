# Bitcoin ETF Fair Value

**Question.** Spot BTC ETFs trade 6.5 hours a day, bitcoin trades 24/7. How closely do ETF prices track fair value, why do some funds hold persistent premiums, and is any of it tradeable after costs?

## Setup

```bash
git clone https://github.com/jennyjin0621/btc-etf-fair-value.git && cd btc-etf-fair-value
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q                          # should pass, runs on synthetic data
python scripts/demo_synthetic.py   # full pipeline on data with a planted premium
jupyter notebook notebooks/00_sanity_check.ipynb
```

All data is free. No API keys needed.

## Layout

```
src/btcetf/
  data.py        loaders. BTC spot (CCXT), ETF bars (yfinance), issuer NAV parser
  fairvalue.py   BTC per share, fee decay fit, intraday fair value, half-life, weekend gaps
  synthetic.py   fake market with KNOWN premium / fee / half-life for testing
  universe.py    ETF tickers, issuers, sponsor fees (verify these!)
notebooks/00_sanity_check.ipynb   week 1 notebook, start here
scripts/demo_synthetic.py         end to end run on synthetic data
tests/                            pytest, synthetic + parser fixtures
data/raw/                         put issuer NAV downloads here (git-ignored)
```

## Where to go

- [ ] **Week 1 (everyone).** Run the sanity notebook for IBIT. Reproduce the issuer's daily premium within ~2 bps, check the fee decay fit against the stated fee, and start the daily 1-min data collector.
- **After that, it's open.** Directions I think are interesting (pick, combine, or pitch your own):
  - Compare funds. Why are some persistently rich or cheap? Fees, APs, custody, cash vs in-kind creation.
  - Intraday fair value. Size and half-life of the premium vs the bid/ask spread.
  - The weekend gap. Does the Monday open fully price the weekend BTC move?
  - Flows and creations. Do premiums drive creations, and do creations close premiums?
- Bring back a notebook that runs from a fresh clone and a short memo with an honest, cost-adjusted verdict.

## Rules of thumb

- Every new function gets a test on synthetic data first. If you cannot recover a premium you planted, you will not find one in the market.
- Never use a price you could not have seen at that moment. `price_asof` exists for this reason.
- Report premiums next to the bid/ask spread. A 10 bp signal inside a 5 bp spread with creation costs is not an edge.
- Keep notebooks thin. Move anything reusable into `src/btcetf/`.
