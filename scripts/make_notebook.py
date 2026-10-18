"""Builds notebooks/00_sanity_check.ipynb (kept as a script so diffs stay readable)."""
import nbformat as nbf
from pathlib import Path

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell
cells = [
md("""# 00 Sanity check

Goal for week 1 is boring on purpose. Get the data in, reproduce numbers the issuers already publish, and make sure your clocks line up. If you cannot reproduce the issuer's own premium/discount, nothing after this is trustworthy.

Before running, download IBIT's NAV history into `data/raw/` (see `data/raw/README.md`)."""),
code("""import sys; sys.path.insert(0, "../src")
import pandas as pd, matplotlib.pyplot as plt
from btcetf import data, fairvalue as fv
from btcetf.universe import ETFS
TICKER = "IBIT\""""),
md("## 1. BTC spot (1m candles, free from Coinbase via CCXT)"),
code("""end = pd.Timestamp.utcnow().floor("D")
start = end - pd.Timedelta(days=6)
btc = data.load_btc_spot(str(start.date()), str(end.date()))
btc.close.plot(title="BTC/USD 1m"); btc.tail()"""),
md("## 2. ETF minute bars (Yahoo, last 7 days only at 1m)"),
code("""etf = data.load_etf_bars(TICKER, interval="1m", period="7d")
etf.close.plot(title=f"{TICKER} 1m"); etf.tail()"""),
md("""## 3. Reproduce the daily premium/discount

Merge yfinance daily closes into the issuer NAV file and compare to what the issuer publishes on its site. Write down any day where you disagree by more than ~2 bps and figure out why."""),
code("""nav = data.load_issuer_nav("../data/raw/IBIT.xls")   # change to your file name
px = data.load_etf_bars(TICKER, interval="1d", period="max")
px.index = px.index.tz_convert("America/New_York").tz_localize(None).normalize()
nav = nav.join(px["close"].rename("yf_close"), how="inner")
if "close" not in nav: nav["close"] = nav["yf_close"]
nav["premium_bps"] = fv.daily_premium(nav)
nav.premium_bps.plot(title=f"{TICKER} daily premium to NAV, bps"); nav.premium_bps.describe()"""),
md("""## 4. Back out BTC per share and check it against the sponsor fee

NAV / BTC price at 4pm ET should decay at roughly the sponsor fee. Daily BTC history from step 1 only covers a few days, so pull a longer window (1h candles are fine here)."""),
code("""btc_h = data.load_btc_spot(str(nav.index[0].date()), str(end.date()), timeframe="1h")
bps = fv.implied_btc_per_share(nav.nav, btc_h.close)
print(fv.fit_fee_decay(bps), "stated fee", ETFS[TICKER]["fee"])
bps.plot(title="Implied BTC per share")"""),
md("## 5. Intraday fair value and premium"),
code("""out = fv.intraday_fair_value(etf.close, btc.close, bps)
out.premium_bps.plot(title=f"{TICKER} intraday premium, bps")
print("mean", out.premium_bps.mean(), "half-life (min)", fv.ar1_half_life(out.premium_bps))"""),
md("## 6. Weekend gaps"),
code("""daily = data.load_etf_bars(TICKER, interval="1d", period="1y")
daily.index = daily.index.tz_convert("America/New_York").tz_localize(None).normalize()
gaps = fv.weekend_gaps(daily, btc_h.close)
gaps.plot.scatter("btc_ret", "etf_gap", title="Monday gap vs weekend BTC move"); gaps.describe()"""),
md("""## Questions to answer before week 2

1. Does your daily premium match the issuer's within a couple of bps? If not, is it the closing price, the NAV timing, or the benchmark?
2. Does the implied fee match the stated fee? What does the residual noise (in bps) tell you about using a single exchange as the BTC reference?
3. Is the intraday premium you measure larger than IBIT's bid/ask spread? Check the spread before calling anything an edge.
4. What timezone is each series in? Plot one hour of ETF and BTC on the same axis and convince yourself they line up."""),
]
nb = nbf.v4.new_notebook(); nb["cells"] = cells
Path(__file__).resolve().parents[1].joinpath("notebooks", "00_sanity_check.ipynb").write_text(nbf.writes(nb))
