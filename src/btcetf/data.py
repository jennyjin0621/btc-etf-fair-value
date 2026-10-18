"""Data loaders. Everything here uses free, public sources.

- BTC spot candles: any exchange supported by CCXT (default Coinbase Exchange)
- ETF bars: Yahoo Finance via yfinance (1m bars only go back ~30 days, 7 days per request;
  5m back ~60 days; 1h back ~2 years; daily back to launch)
- Issuer NAV history: downloaded by hand from each issuer site into data/raw/,
  then parsed with `load_issuer_nav` (handles csv, xlsx and iShares' xml-style .xls)

Downloads are cached in data/cache/ so you are not hammering free APIs.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "cache"
RAW = ROOT / "data" / "raw"
ET = "America/New_York"


def _cache_path(name: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    return CACHE / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', name)}.csv"


# --------------------------------------------------------------------------
# BTC spot
# --------------------------------------------------------------------------
def load_btc_spot(start: str, end: str, timeframe: str = "1m",
                  exchange: str = "coinbaseexchange", symbol: str = "BTC/USD",
                  use_cache: bool = True) -> pd.DataFrame:
    """OHLCV candles from a crypto exchange, indexed by UTC timestamp.

    Exchanges differ in how much history they serve. Coinbase Exchange and
    Bitstamp serve long 1m history. Kraken only serves the latest 720 candles.
    """
    import ccxt  # imported lazily so tests run without it

    path = _cache_path(f"{exchange}_{symbol}_{timeframe}_{start}_{end}")
    if use_cache and path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True)

    ex = getattr(ccxt, exchange)({"enableRateLimit": True})
    since = int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)
    end_ms = int(pd.Timestamp(end, tz="UTC").timestamp() * 1000)
    step = ex.parse_timeframe(timeframe) * 1000
    rows = []
    while since < end_ms:
        batch = ex.fetch_ohlcv(symbol, timeframe, since=since, limit=300)
        if not batch:
            since += 300 * step  # gap in exchange data, skip ahead
            continue
        rows.extend(batch)
        since = batch[-1][0] + step
        time.sleep(ex.rateLimit / 1000)

    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df = df.drop_duplicates("ts")
    df = df[df.ts < end_ms]
    df.index = pd.to_datetime(df.pop("ts"), unit="ms", utc=True)
    df.index.name = "timestamp"
    df.to_csv(path)
    return df


# --------------------------------------------------------------------------
# ETF prices
# --------------------------------------------------------------------------
def load_etf_bars(ticker: str, interval: str = "1m", period: str | None = "7d",
                  start: str | None = None, end: str | None = None,
                  use_cache: bool = True) -> pd.DataFrame:
    """ETF OHLCV from Yahoo Finance, index converted to UTC."""
    import yfinance as yf

    key = f"yf_{ticker}_{interval}_{period}_{start}_{end}"
    path = _cache_path(key)
    if use_cache and path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True)

    kw = dict(interval=interval, auto_adjust=False, progress=False)
    kw.update({"start": start, "end": end} if start else {"period": period})
    df = yf.download(ticker, **kw)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    idx = pd.DatetimeIndex(df.index)
    df.index = (idx.tz_localize(ET) if idx.tz is None else idx).tz_convert("UTC")
    df.index.name = "timestamp"
    df.to_csv(path)
    return df


# --------------------------------------------------------------------------
# Issuer NAV files
# --------------------------------------------------------------------------
def _read_table(path: Path) -> list[list[str]]:
    """Read csv / xlsx / iShares SpreadsheetML into a list of string rows."""
    suffix = path.suffix.lower()
    text_head = path.read_bytes()[:2000].decode("utf-8", errors="ignore")
    if "<?xml" in text_head or "<ss:Workbook" in text_head or "<Workbook" in text_head:
        # iShares 'xls' downloads are actually XML spreadsheets
        xml = path.read_text(encoding="utf-8", errors="ignore")
        rows = []
        for row in re.findall(r"<ss:Row[^>]*>(.*?)</ss:Row>", xml, flags=re.S) or \
                re.findall(r"<Row[^>]*>(.*?)</Row>", xml, flags=re.S):
            cells = re.findall(r"<(?:ss:)?Data[^>]*>(.*?)</(?:ss:)?Data>", row, flags=re.S)
            rows.append([re.sub(r"<[^>]+>", "", c).strip() for c in cells])
        return rows
    if suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path, header=None, dtype=str)
        return df.fillna("").values.tolist()
    import csv
    with open(path, newline="", encoding="utf-8-sig", errors="ignore") as f:
        return [row for row in csv.reader(f)]


def load_issuer_nav(path: str | Path) -> pd.DataFrame:
    """Parse an issuer NAV history file into columns [nav, shares_outstanding?, close?].

    Works by finding the first row that has both a 'date' column and a 'nav'
    column, so it copes with the junk header lines issuers like to add.
    Check the output against the issuer website for a few dates!
    """
    rows = _read_table(Path(path))
    hdr_i = None
    for i, r in enumerate(rows[:200]):
        low = [str(c).strip().lower() for c in r]
        if any("date" in c for c in low) and any(c == "nav" or "nav" in c.split() or
                                                 c.startswith("nav") for c in low):
            hdr_i = i
            break
    if hdr_i is None:
        raise ValueError(f"Could not find a header row with 'date' and 'nav' in {path}")

    header = [str(c).strip().lower() for c in rows[hdr_i]]
    body = [r + [""] * (len(header) - len(r)) for r in rows[hdr_i + 1:] if any(str(c).strip() for c in r)]
    df = pd.DataFrame([r[:len(header)] for r in body], columns=header)

    def pick(*keys):
        for c in df.columns:
            if all(k in c for k in keys):
                return c
        return None

    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df[pick("date")], errors="coerce", format="mixed")
    out["nav"] = pd.to_numeric(df[pick("nav")].str.replace(r"[$,]", "", regex=True), errors="coerce")
    so = pick("shares", "outstanding")
    if so:
        out["shares_outstanding"] = pd.to_numeric(df[so].str.replace(",", ""), errors="coerce")
    cl = pick("clos") or pick("market", "price")
    if cl:
        out["close"] = pd.to_numeric(df[cl].str.replace(r"[$,]", "", regex=True), errors="coerce")
    out = out.dropna(subset=["date", "nav"]).set_index("date").sort_index()
    return out[~out.index.duplicated()]
