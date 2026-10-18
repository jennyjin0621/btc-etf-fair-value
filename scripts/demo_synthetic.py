"""Run the full pipeline on synthetic data with a planted premium.

    python scripts/demo_synthetic.py

Saves figures/demo_synthetic.png. If the numbers printed here do not match the
planted truth, fix your code before touching real data.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from btcetf import fairvalue as fv
from btcetf.synthetic import make_market

m = make_market(days=30)
bps = fv.implied_btc_per_share(m["nav"], m["btc"])
fit = fv.fit_fee_decay(bps)
out = fv.intraday_fair_value(m["etf"], m["btc"], bps)
gaps = fv.weekend_gaps(m["daily"], m["btc"])

print(f"implied fee     {fit['implied_annual_fee']:.4%}   (truth {m['truth']['fee']:.4%})")
print(f"mean premium    {out.premium_bps.mean():.1f} bps  (truth {m['truth']['premium_bps']:.1f})")
print(f"half-life       {fv.ar1_half_life(out.premium_bps):.1f} min  (truth {m['truth']['half_life']:.1f})")
print(f"weekend gaps    {len(gaps)}, median |residual| {gaps.residual_bps.abs().median():.1f} bps")

fig, ax = plt.subplots(2, 1, figsize=(9, 6))
day = out.index.tz_convert("America/New_York").date == out.index.tz_convert("America/New_York").date[0]
ax[0].plot(out.index[day], out.etf[day], label="ETF")
ax[0].plot(out.index[day], out.fair[day], label="fair value", alpha=0.8)
ax[0].set_title("One day of ETF price vs fair value (synthetic)")
ax[0].legend()
ax[1].hist(out.premium_bps, bins=80)
ax[1].set_title("Intraday premium distribution, bps")
fig.tight_layout()
(ROOT / "figures").mkdir(exist_ok=True)
fig.savefig(ROOT / "figures" / "demo_synthetic.png", dpi=120)
print("saved figures/demo_synthetic.png")
