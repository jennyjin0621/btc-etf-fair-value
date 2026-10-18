"""Tests on synthetic data with known answers. Run with `pytest -q`."""
import numpy as np
import pandas as pd

from btcetf import fairvalue as fv
from btcetf.synthetic import make_market


def test_recovers_fee_from_nav():
    m = make_market(days=60)
    bps = fv.implied_btc_per_share(m["nav"], m["btc"])
    fit = fv.fit_fee_decay(bps)
    assert abs(fit["implied_annual_fee"] - m["truth"]["fee"]) < 5e-4


def test_recovers_planted_premium_and_half_life():
    m = make_market(days=20)
    bps = fv.implied_btc_per_share(m["nav"], m["btc"])
    out = fv.intraday_fair_value(m["etf"], m["btc"], bps)
    # BPS known at bar time is the previous strike, so allow ~1bp of fee drift
    assert abs(out.premium_bps.mean() - m["truth"]["premium_bps"]) < 2
    hl = fv.ar1_half_life(out.premium_bps)
    assert abs(hl - m["truth"]["half_life"]) < 2


def test_price_asof_never_looks_ahead():
    s = pd.Series([1.0, 2.0], index=pd.to_datetime(["2026-01-01 10:00", "2026-01-01 10:02"], utc=True))
    t = pd.DatetimeIndex(pd.to_datetime(["2026-01-01 10:01"], utc=True))
    assert fv.price_asof(s, t).iloc[0] == 1.0


def test_weekend_gaps_shape():
    m = make_market(days=21)
    g = fv.weekend_gaps(m["daily"], m["btc"])
    assert len(g) >= 2 and (g.days >= 2).all()
    # planted premium is stable, so ETF gap should track BTC within tens of bps
    assert g.residual_bps.abs().median() < 50
