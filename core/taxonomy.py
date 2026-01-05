from __future__ import annotations

# Controlled vocabularies for normalization (extend as needed)
GEOGRAPHIC_MARKETS = ["US", "Europe", "APAC"]

INVESTMENT_APPROACHES = ["Fundamental", "Systematic"]

ASSET_CLASSES = ["Equity", "Credit", "Macro", "Rates", "Commodities", "Volatility", "FX"]

SECTORS = [
    "Technology",
    "Healthcare",
    "Financial Services",
    "Energy",
    "Industrials",
    "Consumer",
    "TMT",
    "Real Estate",
    "Utilities",
]

ROLES = [
    "Junior Analyst",
    "Research Analyst",
    "Quant Research",
    "Quant Trading",
    "Trader",
    "Credit Analyst",
    "Macro Research",
    "Data",
]

DEGREE_LEVELS = ["High School", "Bachelors", "Masters", "PhD", "Other"]

# Simple synonym maps (expand over time)
SYN_SECTOR = {
    "financials": "Financial Services",
    "finserv": "Financial Services",
    "tech": "Technology",
    "tmt": "TMT",
    "health care": "Healthcare",
    "healthcare": "Healthcare",
}

SYN_APPROACH = {
    "quant": "Systematic",
    "systematic": "Systematic",
    "discretionary": "Fundamental",
    "fundamental": "Fundamental",
}

SYN_GEO = {
    "usa": "US",
    "united states": "US",
    "us": "US",
    "u.s.": "US",
    "europe": "Europe",
    "emea": "Europe",
    "apac": "APAC",
    "asia": "APAC",
}

SYN_ASSET_CLASS = {
    "equities": "Equity",
    "equity": "Equity",
    "credit": "Credit",
    "macro": "Macro",
    "rates": "Rates",
    "commodities": "Commodities",
    "fx": "FX",
    "vol": "Volatility",
}
