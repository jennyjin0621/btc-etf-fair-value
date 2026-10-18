"""Fair value and premium utilities.

Conventions
- All timestamps are tz-aware. Intraday series are indexed in UTC.
- Premiums are in basis points. premium_bps = (price / fair - 1) * 1e4
- btc_per_share (BPS) is BTC held per ETF share. It shrinks slowly because the
  sponsor fee is paid by selling BTC.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ET = "America/New_York"


def price_asof(series: pd.Series, times: pd.DatetimeIndex) -> pd.Series:
    """Last observed value of `series` at or before each time in `times`.
    Using asof (not nearest) avoids peeking at future prices."""
    s = series.dropna().sort_index()
    pos = s.index.searchsorted(times, side="right") - 1
    vals = np.where(pos >= 0, s.values[np.clip(pos, 0, None)], np.nan)
    return pd.Series(vals, index=times)


def daily_premium(nav: pd.DataFrame) -> pd.Series:
    """Issuer-style daily premium using the ETF closing price and the official NAV."""
    if "close" not in nav:
        raise ValueError("NAV frame needs a 'close' column (merge in yfinance daily closes)")
    return (nav["close"] / nav["nav"] - 1) * 1e4


def implied_btc_per_share(nav: pd.Series, btc_close: pd.Series, fix_time: str = "16:00") -> pd.Series:
    """Back out BTC per share as NAV / BTC price at the NAV strike time (ET).

    Issuers strike NAV off a benchmark (e.g. a CF Benchmarks index around 4pm ET),
    not off one exchange, so expect a few bps of noise here. That noise is part
    of the lesson.
    """
    h, m = map(int, fix_time.split(":"))
    strike = pd.DatetimeIndex([pd.Timestamp(d.date(), tz=ET).replace(hour=h, minute=m) for d in nav.index])
    px = price_asof(btc_close, strike.tz_convert("UTC"))
    return pd.Series(nav.values / px.values, index=nav.index, name="btc_per_share")


def fit_fee_decay(bps: pd.Series) -> dict:
    """Fit log(BPS) = a + b * years. Implied annual fee is 1 - exp(b).
    If this does not roughly match the stated sponsor fee, something is off
    in your NAV or BTC data (or the fund changed its fee / had a fee waiver)."""
    s = bps.dropna()
    s = s[s > 0]
    years = np.asarray((s.index - s.index[0]).days / 365.25, dtype=float)
    b, a = np.polyfit(years, np.log(s.values), 1)
    resid = np.log(s.values) - (a + b * years)
    return {"bps0": float(np.exp(a)), "implied_annual_fee": float(1 - np.exp(b)),
            "resid_bps_std": float(resid.std() * 1e4)}


def intraday_fair_value(etf_close: pd.Series, btc_close: pd.Series, bps_daily: pd.Series) -> pd.DataFrame:
    """Fair value of each ETF bar = BTC price (asof) * BTC per share.

    bps_daily is indexed by date; each bar uses the latest BPS struck strictly
    before that trading date (no look-ahead).
    """
    t = etf_close.index
    btc = price_asof(btc_close, t)
    dates = pd.DatetimeIndex(t.tz_convert(ET).date)
    bps_idx = pd.DatetimeIndex(pd.to_datetime(bps_daily.index).date)
    # BPS struck at 4pm on day D is only known after the close, so bars on day D
    # use the previous strike. Shifting by one row enforces that.
    bps = pd.Series(bps_daily.values, index=bps_idx).sort_index().shift(1)
    bps_on = price_asof(bps, dates)
    fair = btc.values * bps_on.values
    out = pd.DataFrame({"etf": etf_close.values, "btc": btc.values,
                        "bps": bps_on.values, "fair": fair}, index=t)
    out["premium_bps"] = (out.etf / out.fair - 1) * 1e4
    return out


def ar1_half_life(x: pd.Series) -> float:
    """Half-life (in bars) of an AR(1) fit to x. Returns inf if not mean reverting."""
    x = x.dropna()
    y, ylag = x.values[1:], x.values[:-1]
    phi = np.polyfit(ylag - ylag.mean(), y - y.mean(), 1)[0]
    return float(np.log(0.5) / np.log(phi)) if 0 < phi < 1 else float("inf")


def weekend_gaps(etf_daily: pd.DataFrame, btc_close: pd.Series) -> pd.DataFrame:
    """For each session that follows a gap of 2+ calendar days (weekends, holidays),
    compare the ETF's close-to-open return to BTC's return over the same window.

    etf_daily needs 'open' and 'close' columns indexed by trading date.
    beta near 1 and small residuals means the open prices in the weekend move.
    """
    d = etf_daily.sort_index()
    idx = pd.DatetimeIndex(d.index)
    rows = []
    for prev, cur in zip(idx[:-1], idx[1:]):
        if (cur - prev).days < 2:
            continue
        t0 = pd.Timestamp(prev.date(), tz=ET).replace(hour=16).tz_convert("UTC")
        t1 = pd.Timestamp(cur.date(), tz=ET).replace(hour=9, minute=30).tz_convert("UTC")
        b = price_asof(btc_close, pd.DatetimeIndex([t0, t1]))
        rows.append({"date": cur, "days": (cur - prev).days,
                     "etf_gap": d.loc[cur, "open"] / d.loc[prev, "close"] - 1,
                     "btc_ret": b.iloc[1] / b.iloc[0] - 1})
    out = pd.DataFrame(rows).set_index("date")
    out["residual_bps"] = (out.etf_gap - out.btc_ret) * 1e4
    return out
