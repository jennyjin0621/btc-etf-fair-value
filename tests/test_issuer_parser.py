"""The issuer files are messy. These fixtures mimic the common layouts."""
from btcetf.data import load_issuer_nav

CSV = """iShares Bitcoin Trust ETF
Fund Holdings as of,"Oct 17, 2026"

Date,NAV per Share,Shares Outstanding,Closing Price
"Oct 16, 2026",55.12,"1,000,000",55.20
"Oct 15, 2026",54.01,"990,000",54.05
"""

XML = """<?xml version="1.0"?>
<ss:Workbook xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
<ss:Worksheet ss:Name="Historical"><ss:Table>
<ss:Row><ss:Cell><ss:Data ss:Type="String">As Of</ss:Data></ss:Cell><ss:Cell><ss:Data ss:Type="String">NAV per Share</ss:Data></ss:Cell><ss:Cell><ss:Data ss:Type="String">Shares Outstanding</ss:Data></ss:Cell></ss:Row>
<ss:Row><ss:Cell><ss:Data ss:Type="String">Date</ss:Data></ss:Cell><ss:Cell><ss:Data ss:Type="String">NAV</ss:Data></ss:Cell><ss:Cell><ss:Data ss:Type="String">Shares Outstanding</ss:Data></ss:Cell></ss:Row>
<ss:Row><ss:Cell><ss:Data ss:Type="String">Oct 16, 2026</ss:Data></ss:Cell><ss:Cell><ss:Data ss:Type="Number">55.12</ss:Data></ss:Cell><ss:Cell><ss:Data ss:Type="Number">1000000</ss:Data></ss:Cell></ss:Row>
</ss:Table></ss:Worksheet></ss:Workbook>
"""


def test_csv_with_junk_header(tmp_path):
    p = tmp_path / "ibit.csv"
    p.write_text(CSV)
    df = load_issuer_nav(p)
    assert list(df.nav) == [54.01, 55.12]
    assert "shares_outstanding" in df and "close" in df


def test_ishares_xml_xls(tmp_path):
    p = tmp_path / "ibit.xls"
    p.write_text(XML)
    df = load_issuer_nav(p)
    assert df.nav.iloc[0] == 55.12 and df.shares_outstanding.iloc[0] == 1_000_000
