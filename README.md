# Bitcoin ETF Fair Value

Starter repo for the student research project on spot bitcoin ETF fair value, premiums and the weekend gap. The full project guide (motivation, steps, red flags) is in the PDF your mentor sent.

**Question.** Spot BTC ETFs trade 6.5 hours a day, bitcoin trades 24/7. How closely do ETF prices track fair value, why do some funds hold persistent premiums, and is any of it tradeable after costs?

## Setup

```bash
git clone <this repo> && cd btc-etf-fair-value
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

## Week-by-week checklist

- [ ] **Week 1.** Run the sanity notebook for IBIT. Reproduce the issuer's daily premium within ~2 bps. Fee decay fit matches the stated fee.
- [ ] **Week 2.** Extend to all 6 funds. One table of mean / std / persistence of daily premium per fund.
- [ ] **Week 3.** Intraday fair value. Premium distribution, half-life, and how both compare to the quoted bid/ask spread.
- [ ] **Week 4.** Weekend and holiday gaps. Does the Monday open fully price the weekend BTC move? Does the residual survive the spread?
- [ ] **Week 5.** Cross-section. Explain premium differences with fees, size, AP and custody setup, and the move from cash to in-kind creations.
- [ ] **Week 6.** Write-up. Short memo plus clean notebook with an honest, cost-adjusted verdict.

## Rules of thumb

- Every new function gets a test on synthetic data first. If you cannot recover a premium you planted, you will not find one in the market.
- Never use a price you could not have seen at that moment. `price_asof` exists for this reason.
- Report premiums next to the bid/ask spread. A 10 bp signal inside a 5 bp spread with creation costs is not an edge.
- Keep notebooks thin. Move anything reusable into `src/btcetf/`.
