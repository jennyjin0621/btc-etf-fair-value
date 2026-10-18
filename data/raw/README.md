# Raw issuer files (download by hand)

Issuer NAV histories are free but are not served through a clean API, so grab them from the product pages and drop them here. They are git-ignored.

| Fund | Where to get it |
|---|---|
| IBIT | ishares.com IBIT product page, "Data Download" / historical NAV link. The file says .xls but is really XML, `load_issuer_nav` handles it |
| FBTC | fidelity.com FBTC page, performance / NAV history |
| GBTC, BTC | etfs.grayscale.com product pages, historical NAV / premium download |
| ARKB | ark-funds.com ARKB page, fund holdings / NAV history |
| BITB | bitbetf.com, NAV history |

Name them like `IBIT.xls`, `FBTC.csv`, etc. Then run

```python
from btcetf.data import load_issuer_nav
load_issuer_nav("data/raw/IBIT.xls").tail()
```

and check three random dates against the issuer website. Issuers change their download formats without warning, so if the parser breaks, fix it and open a PR.
