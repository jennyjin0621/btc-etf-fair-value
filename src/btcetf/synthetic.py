"""Synthetic data with KNOWN answers, used by tests and by scripts/demo_synthetic.py.

Use it to check your code before touching real data: if your pipeline cannot
recover a premium you planted yourself, it will not find one in the market.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ET = "America/New_York"


def make_market(days: int = 30, fee: float = 0.0025, bps0: float = 0.00057,
                true_premium_bps: float = 20.0, noise_bps: float = 5.0,
                phi: float = 0.9, seed: int = 0):
    rng = np.random.default_rng(seed)
    t = pd.date_range("2026-01-05", periods=days * 1440, freq="1min", tz="UTC")
    ret = rng.normal(0, 0.0006, len(t))
    btc = pd.Series(90_000 * np.exp(np.cumsum(ret)), index=t, name="close")

    # trading-day calendar (weekdays only), NAV struck at 4pm ET
    dates = pd.bdate_range(t[0].tz_convert(ET).date(), t[-1].tz_convert(ET).date())
    years = (dates - dates[0]).days / 365.25
    bps = pd.Series(bps0 * (1 - fee) ** years, index=dates)

    # ETF minute bars 9:30-16:00 ET with AR(1) premium around true_premium_bps
    et = t.tz_convert(ET)
    mask = (et.weekday < 5) & (et.time >= pd.Timestamp("09:30").time()) & (et.time < pd.Timestamp("16:00").time())
    tt = t[mask]
    prem = np.empty(len(tt))
    prem[0] = true_premium_bps
    for i in range(1, len(tt)):
        prem[i] = true_premium_bps + phi * (prem[i - 1] - true_premium_bps) + rng.normal(0, noise_bps)
    d = pd.DatetimeIndex(tt.tz_convert(ET).date)
    fair = btc.loc[tt].values * bps.reindex(d).values
    etf = pd.Series(fair * (1 + prem / 1e4), index=tt, name="close")

    strike = pd.DatetimeIndex([pd.Timestamp(x.date(), tz=ET).replace(hour=16) for x in dates]).tz_convert("UTC")
    strike = strike[strike <= t[-1]]
    nav = pd.Series(btc.reindex(strike, method="ffill").values * bps.iloc[:len(strike)].values,
                    index=dates[:len(strike)], name="nav")

    daily = etf.groupby(pd.DatetimeIndex(etf.index.tz_convert(ET).date)).agg(["first", "last"])
    daily.columns = ["open", "close"]
    return {"btc": btc, "etf": etf, "nav": nav, "bps": bps, "daily": daily,
            "truth": {"fee": fee, "premium_bps": true_premium_bps,
                      "half_life": np.log(0.5) / np.log(phi)}}
