from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
import re
import datetime as dt
from .base import LLMProvider

def _find_emails(text: str) -> List[str]:
    return list(dict.fromkeys(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)))

def _find_phones(text: str) -> List[str]:
    phones = re.findall(r"(?:\+?\d{1,3}[-\s]?)?(?:\(?\d{2,4}\)?[-\s]?)?\d{3,4}[-\s]?\d{3,4}", text)
    cleaned=[]
    for p in phones:
        p2=re.sub(r"\s+", " ", p).strip()
        if len(re.sub(r"\D","",p2))>=10:
            cleaned.append(p2)
    out=[]
    for p in cleaned:
        if p not in out:
            out.append(p)
    return out[:3]

_MONTHS = {
    "jan":1,"january":1,"feb":2,"february":2,"mar":3,"march":3,"apr":4,"april":4,"may":5,
    "jun":6,"june":6,"jul":7,"july":7,"aug":8,"august":8,"sep":9,"sept":9,"september":9,
    "oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12
}

def _parse_month_year(s: str) -> Optional[dt.date]:
    s = s.strip().lower()
    # formats: "Jan 2022", "January 2022", "2022"
    m = re.match(r"^(?P<mon>[a-z]{3,9})\s+(?P<yr>\d{4})$", s)
    if m:
        mon = _MONTHS.get(m.group("mon"))
        if mon:
            return dt.date(int(m.group("yr")), mon, 1)
    m = re.match(r"^(?P<yr>\d{4})$", s)
    if m:
        return dt.date(int(m.group("yr")), 1, 1)
    return None

def _extract_date_ranges(text: str) -> List[Tuple[dt.date, dt.date]]:
    """
    Pulls common resume date ranges:
      - Jan 2021 - Mar 2023
      - 2020 - 2022
      - Jun 2019 – Present
    """
    ranges=[]
    # Normalize dash variants
    t = text.replace("–", "-").replace("—", "-")
    # Month Year - Month Year/Present
    pat1 = re.compile(r"(?P<a>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December)\s+\d{4})\s*-\s*(?P<b>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December)\s+\d{4}|Present|Current)",
                       re.IGNORECASE)
    for m in pat1.finditer(t):
        a = _parse_month_year(m.group("a"))
        braw = m.group("b").strip()
        b = dt.date.today().replace(day=1) if braw.lower() in ("present","current") else _parse_month_year(braw)
        if a and b and b >= a:
            ranges.append((a,b))

    # Year - Year/Present
    pat2 = re.compile(r"(?P<a>\d{4})\s*-\s*(?P<b>\d{4}|Present|Current)", re.IGNORECASE)
    for m in pat2.finditer(t):
        a = _parse_month_year(m.group("a"))
        braw = m.group("b").strip()
        b = dt.date.today().replace(day=1) if braw.lower() in ("present","current") else _parse_month_year(braw)
        if a and b and b >= a:
            ranges.append((a,b))

    return ranges

def _estimate_years_experience(text: str) -> Optional[float]:
    # First, explicit "X years"
    m = re.search(r"\b(\d{1,2})(?:\+)?\s+years?\b", text, re.IGNORECASE)
    if m:
        try:
            v = float(m.group(1))
            if 0 <= v <= 60:
                return v
        except Exception:
            pass

    # Otherwise, compute from earliest start to latest end across detected ranges
    ranges = _extract_date_ranges(text)
    if not ranges:
        return None
    start = min(a for a,_ in ranges)
    end = max(b for _,b in ranges)
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if months < 0:
        return None
    years = round(months / 12.0, 1)
    if years > 60:
        years = 60.0
    return years

def _infer_approach(text: str) -> List[str]:
    t = text.lower()
    systematic_terms = [
        "quant", "systematic", "alpha", "signals", "backtest", "back-testing", "factor model",
        "regression", "time series", "machine learning", "ml", "xgboost", "random forest",
        "pytorch", "tensorflow", "feature engineering", "stat arb", "statistical arbitrage"
    ]
    fundamental_terms = [
        "fundamental", "valuation", "dcf", "comps", "earnings", "10-k", "10q", "10-q",
        "industry research", "channel checks", "modeling", "financial model", "pitch book"
    ]
    sys_hit = any(k in t for k in systematic_terms)
    fund_hit = any(k in t for k in fundamental_terms)
    out=[]
    if fund_hit:
        out.append("Fundamental")
    if sys_hit:
        out.append("Systematic")
    # If nothing hit, leave empty (don't guess)
    return out

def _infer_sectors(text: str) -> List[str]:
    t = text.lower()
    sectors=[]
    def add(name, kws):
        nonlocal sectors
        if any(k in t for k in kws):
            sectors.append(name)

    add("Technology", ["software","saas","cloud","ai","artificial intelligence","data platform","semiconductor","tech"])
    add("Healthcare", ["healthcare","biotech","pharma","clinical","hospital","medical device"])
    add("Financial Services", ["investment bank","banking","bank","financial","fintech","insurance","asset management","private equity"])
    add("Energy", ["oil","gas","upstream","downstream","refining","energy","power generation","utilities"])
    add("Industrials", ["manufacturing","industrial","aerospace","defense","automation","supply chain","logistics"])
    add("Consumer", ["consumer","retail","e-commerce","ecommerce","cpg","brands","marketplace"])

    # unique preserve order
    seen=set(); out=[]
    for s in sectors:
        if s not in seen:
            seen.add(s); out.append(s)
    return out

def _infer_geo_market(text: str) -> Optional[str]:
    t = text.lower()
    if re.search(r"\b(new york|nyc|boston|chicago|san francisco|california|usa|u\.s\.|united states)\b", t):
        return "US"
    if re.search(r"\b(london|uk|united kingdom|england|paris|france|germany|frankfurt|europe|emea)\b", t):
        return "Europe"
    if re.search(r"\b(singapore|hong kong|india|mumbai|bangalore|tokyo|japan|china|shanghai|seoul|asia|apac)\b", t):
        return "APAC"
    return None

def _infer_skills(text: str) -> Dict[str, List[str]]:
    t = text.lower()
    def has(word): return re.search(rf"\b{re.escape(word.lower())}\b", t) is not None

    programming = [s for s in ["Python","C++","Java","R","Julia"] if has(s)]
    data = [s for s in ["SQL","Pandas","Spark","Snowflake","Airflow"] if has(s)]
    ml = []
    for s in ["Machine Learning","Deep Learning","XGBoost","PyTorch","TensorFlow","NLP"]:
        if s.lower().replace(" ","") in t.replace(" ","") or has(s):
            ml.append(s)
    finance = []
    for s in ["DCF","Valuation","Factor Models","Options","Derivatives","Risk"]:
        if s.lower().replace(" ","") in t.replace(" ","") or has(s):
            finance.append(s)
    tools = []
    for s in ["Bloomberg","FactSet","Capital IQ","Refinitiv","Koyfin"]:
        if s.lower().replace(" ","") in t.replace(" ","") or has(s):
            tools.append(s)

    # de-dupe preserve order
    def uniq(xs):
        out=[]; seen=set()
        for x in xs:
            if x not in seen:
                seen.add(x); out.append(x)
        return out
    return {
        "programming": uniq(programming),
        "data": uniq(data),
        "ml": uniq(ml),
        "finance": uniq(finance),
        "tools": uniq(tools),
        "other": []
    }

class MockProvider(LLMProvider):
    """
    Deterministic parser for demo/testing (no API). Uses heuristics to populate the schema.
    Replace with a real LLM provider for production accuracy.
    """
    def parse_resume(self, resume_id: str, resume_text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
        name = lines[0] if lines else None

        emails = _find_emails(resume_text)
        phones = _find_phones(resume_text)

        geo = _infer_geo_market(resume_text)
        approaches = _infer_approach(resume_text)
        sectors = _infer_sectors(resume_text)
        years = _estimate_years_experience(resume_text)
        skills = _infer_skills(resume_text)

        parsed = {
            "resume_id": resume_id,
            "candidate": {
                "full_name": name,
                "emails": emails,
                "phones": phones,
                "location_current": {"city": None, "region": None, "country": None},
                "citizenship": [],
                "work_authorization": {"us": None, "uk": None, "eu": None, "other": None},
                "linkedin": None,
                "github": None,
                "languages_spoken": []
            },
            "target_fit": {
                "geographic_markets": [geo] if geo else [],
                "investment_approaches": approaches,
                "asset_classes": ["Equity"],
                "sectors": sectors,
                "roles": ["Junior Analyst"]
            },
            "summary": {
                "years_experience": years,
                "current_title": None,
                "current_employer": None,
                "education_level": None,
                "highlights": []
            },
            "education": [],
            "experience": [],
            "skills": skills,
            "certifications": [],
            "metadata": {
                "parsed_at": dt.datetime.utcnow().isoformat() + "Z",
                "parser_version": "mock_v2",
                "quality": {"confidence": 0.6, "notes": ["Heuristic mock parser (improve by switching to LLM provider)."]}
            },
            "evidence": {
                "field_to_snippets": {
                    "candidate.full_name": [lines[0]] if lines else [],
                    "candidate.emails": emails[:1] if emails else [],
                    "summary.years_experience": [str(years)] if years is not None else [],
                    "target_fit.investment_approaches": approaches[:1] if approaches else [],
                    "target_fit.sectors": sectors[:2] if sectors else [],
                }
            }
        }
        return parsed
