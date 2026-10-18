"""Spot bitcoin ETF universe.

Sponsor fees change (fee waivers expire, cuts happen). Treat these as a
starting point and VERIFY each one on the issuer's site before using them in
any fair value calculation. Record the date you checked.
"""

ETFS = {
    # ticker: issuer, approx annual sponsor fee (decimal), issuer product page
    "IBIT": {"issuer": "iShares (BlackRock)", "fee": 0.0025,
             "url": "https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf"},
    "FBTC": {"issuer": "Fidelity", "fee": 0.0025,
             "url": "https://www.fidelity.com/etfs/bitcoin"},
    "GBTC": {"issuer": "Grayscale", "fee": 0.0150,
             "url": "https://etfs.grayscale.com/gbtc"},
    "BTC":  {"issuer": "Grayscale (Mini)", "fee": 0.0015,
             "url": "https://etfs.grayscale.com/btc"},
    "ARKB": {"issuer": "ARK / 21Shares", "fee": 0.0021,
             "url": "https://www.ark-funds.com/funds/arkb"},
    "BITB": {"issuer": "Bitwise", "fee": 0.0020,
             "url": "https://bitbetf.com"},
}

TICKERS = list(ETFS)
