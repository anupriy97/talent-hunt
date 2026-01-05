from __future__ import annotations
from typing import Any, Dict, List, Optional
import re
from . import taxonomy

def _norm_str(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

def normalize_market(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = _norm_str(value)
    v = taxonomy.SYN_GEO.get(v, value)
    # Map any unknown into itself (but try to keep to the controlled list)
    if v in taxonomy.GEOGRAPHIC_MARKETS:
        return v
    # Heuristic: if country suggests market
    if any(k in v.lower() for k in ["united states", "usa", "new york", "boston", "chicago"]):
        return "US"
    if any(k in v.lower() for k in ["london", "uk", "france", "germany", "europe"]):
        return "Europe"
    if any(k in v.lower() for k in ["singapore", "hong kong", "india", "japan", "china", "asia"]):
        return "APAC"
    return v

def normalize_approach(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = _norm_str(value)
    v = taxonomy.SYN_APPROACH.get(v, value)
    if v in taxonomy.INVESTMENT_APPROACHES:
        return v
    # fallback
    if "quant" in v or "system" in v:
        return "Systematic"
    return "Fundamental"

def normalize_sector_list(values: List[str]) -> List[str]:
    out = []
    for s in values or []:
        if not s:
            continue
        v = _norm_str(s)
        mapped = taxonomy.SYN_SECTOR.get(v, s)
        # Title-case the mapped string but keep known controlled terms
        if mapped in taxonomy.SECTORS:
            out.append(mapped)
        else:
            out.append(mapped.title())
    # unique preserve order
    seen = set()
    uniq = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq

def normalize_asset_class_list(values: List[str]) -> List[str]:
    out = []
    for s in values or []:
        if not s:
            continue
        v = _norm_str(s)
        mapped = taxonomy.SYN_ASSET_CLASS.get(v, s)
        if mapped in taxonomy.ASSET_CLASSES:
            out.append(mapped)
        else:
            out.append(mapped.title())
    seen=set(); uniq=[]
    for x in out:
        if x not in seen:
            seen.add(x); uniq.append(x)
    return uniq

def clamp_years_exp(y: Any) -> Optional[float]:
    try:
        f = float(y)
        if f < 0:
            return None
        if f > 60:
            return 60.0
        return round(f, 1)
    except Exception:
        return None
