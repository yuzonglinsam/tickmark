"""Map SEC SIC codes to broad sectors (approximate; SIC-based, not GICS)."""
from __future__ import annotations

SECTORS = ("Information Technology", "Communication Services", "Consumer Discretionary",
           "Consumer Staples", "Health Care", "Industrials", "Energy", "Materials", "Utilities",
           "Real Estate", "Financials", "Other")

# A few large issuers whose SIC code sits far from how investors classify them.
OVERRIDES = {
    "GOOGL": "Communication Services", "GOOG": "Communication Services", "META": "Communication Services",
    "NFLX": "Communication Services", "DIS": "Communication Services", "BIDU": "Communication Services",
    "NTES": "Communication Services", "BILI": "Communication Services", "TME": "Communication Services",
    "WB": "Communication Services", "AMZN": "Consumer Discretionary", "BABA": "Consumer Discretionary",
    "JD": "Consumer Discretionary", "PDD": "Consumer Discretionary", "TCOM": "Consumer Discretionary",
    "V": "Financials", "MA": "Financials", "PYPL": "Financials", "TSLA": "Consumer Discretionary",
    "UBER": "Industrials", "BKNG": "Consumer Discretionary", "ABNB": "Consumer Discretionary",
    "WMT": "Consumer Staples", "COST": "Consumer Staples", "TGT": "Consumer Staples",
}


def sector(sic: str | int | None, ticker: str = "") -> str:
    if ticker in OVERRIDES:
        return OVERRIDES[ticker]
    try:
        c = int(sic)
    except (TypeError, ValueError):
        return "Other"
    if c < 1000:
        return "Consumer Staples"
    if 1300 <= c < 1400:
        return "Energy"
    if c < 1500:
        return "Materials"
    if c < 1800:
        return "Industrials"
    if c < 2200:
        return "Consumer Staples"
    if c < 2600:
        return "Consumer Discretionary"
    if c < 2700:
        return "Materials"
    if c < 2800:
        return "Communication Services"
    if 2830 <= c <= 2836:
        return "Health Care"
    if 2840 <= c <= 2844:
        return "Consumer Staples"
    if c < 2900:
        return "Materials"
    if c < 3000:
        return "Energy"
    if c < 3200:
        return "Consumer Discretionary"
    if c < 3400:
        return "Materials"
    if c < 3500:
        return "Industrials"
    if 3570 <= c <= 3579:
        return "Information Technology"
    if c < 3600:
        return "Industrials"
    if 3660 <= c <= 3699:
        return "Information Technology"
    if c < 3700:
        return "Industrials"
    if 3710 <= c <= 3716 or c == 3751:
        return "Consumer Discretionary"
    if c < 3800:
        return "Industrials"
    if 3840 <= c <= 3851:
        return "Health Care"
    if c < 3900:
        return "Information Technology"
    if c < 4000:
        return "Consumer Discretionary"
    if 4900 <= c < 5000:
        return "Industrials" if c in (4953, 4955, 4959, 4961) else "Utilities"
    if 4800 <= c < 4900:
        return "Communication Services"
    if c < 4900:
        return "Industrials"
    if c == 5122 or 5047 == c:
        return "Health Care"
    if c < 5200:
        return "Industrials"
    if c in (5331, 5399, 5411, 5412, 5900, 5912):
        return "Consumer Staples"
    if c < 6000:
        return "Consumer Discretionary"
    if c < 6500:
        return "Financials"
    if c < 6800:
        return "Real Estate"
    if c < 7300:
        return "Consumer Discretionary"
    if 7370 <= c <= 7379:
        return "Information Technology"
    if c < 7800:
        return "Industrials"
    if c < 8000:
        return "Communication Services"
    if c < 8100:
        return "Health Care"
    if 8731 <= c <= 8734:
        return "Health Care" if c == 8731 else "Industrials"
    if c < 9000:
        return "Industrials"
    return "Other"
