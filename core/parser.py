from __future__ import annotations
from typing import Dict, Any, Tuple, List
import uuid
import datetime as dt

from .extract import extract_resume_text, needs_ocr
from .schema import ParsedResume, json_schema
from .llm_factory import get_provider
from .normalize import normalize_market, normalize_approach, normalize_sector_list, normalize_asset_class_list, clamp_years_exp

def build_search_blob(parsed: Dict[str, Any], resume_text: str) -> str:
    parts: List[str] = []
    cand = parsed.get("candidate", {})
    parts += [cand.get("full_name") or ""]
    parts += (cand.get("emails") or [])
    parts += (cand.get("phones") or [])

    parts += parsed.get("target_fit", {}).get("sectors", []) or []
    parts += parsed.get("target_fit", {}).get("roles", []) or []
    parts += parsed.get("target_fit", {}).get("investment_approaches", []) or []
    parts += parsed.get("target_fit", {}).get("asset_classes", []) or []

    skills = parsed.get("skills", {}) or {}
    for k in ["programming","data","ml","finance","tools","other"]:
        parts += skills.get(k, []) or []

    # experience bullets/employers
    for exp in parsed.get("experience", []) or []:
        parts += [exp.get("employer") or "", exp.get("title") or ""]
        parts += exp.get("bullets", []) or []

    parts.append(resume_text[:5000])  # cap
    blob = " ".join([p for p in parts if p])
    blob = blob.lower()
    return blob

def normalize_for_db(parsed: ParsedResume, resume_text: str, source_filename: str) -> Dict[str, Any]:
    p = parsed.model_dump()

    # Core fields
    full_name = p["candidate"].get("full_name")
    email = (p["candidate"].get("emails") or [None])[0]
    phone = (p["candidate"].get("phones") or [None])[0]
    country = p["candidate"].get("location_current", {}).get("country")

    # Market/approach
    geo_raw = None
    geo_list = (p.get("target_fit", {}) or {}).get("geographic_markets", []) or []
    if geo_list:
        geo_raw = geo_list[0]
    geo_market = normalize_market(geo_raw or country)

    approach_list = (p.get("target_fit", {}) or {}).get("investment_approaches", []) or []
    approach_raw = approach_list[0] if approach_list else None
    approach = normalize_approach(approach_raw)

    # Years exp / degree level
    years_raw = (p.get("summary", {}) or {}).get("years_experience")
    years_exp = clamp_years_exp(years_raw)

    degree_level = (p.get("summary", {}) or {}).get("education_level")

    # Lists
    sectors = normalize_sector_list((p.get("target_fit", {}) or {}).get("sectors", []) or [])
    asset_classes = normalize_asset_class_list((p.get("target_fit", {}) or {}).get("asset_classes", []) or [])
    roles = (p.get("target_fit", {}) or {}).get("roles", []) or []

    skills = p.get("skills", {}) or {}
    rec = {
        "resume_id": p["resume_id"],
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "geo_market": geo_market,
        "country": country,
        "approach": approach,
        "years_experience": years_exp,
        "degree_level": degree_level,
        "sectors_json": __import__("json").dumps(sectors, ensure_ascii=False),
        "asset_classes_json": __import__("json").dumps(asset_classes, ensure_ascii=False),
        "roles_json": __import__("json").dumps(roles, ensure_ascii=False),
        "skills_programming_json": __import__("json").dumps(skills.get("programming", []) or [], ensure_ascii=False),
        "skills_data_json": __import__("json").dumps(skills.get("data", []) or [], ensure_ascii=False),
        "skills_ml_json": __import__("json").dumps(skills.get("ml", []) or [], ensure_ascii=False),
        "skills_finance_json": __import__("json").dumps(skills.get("finance", []) or [], ensure_ascii=False),
        "skills_tools_json": __import__("json").dumps(skills.get("tools", []) or [], ensure_ascii=False),
        "search_blob": build_search_blob(p, resume_text),
        "parsed_json": __import__("json").dumps(p, ensure_ascii=False),
        "source_filename": source_filename,
    }
    return rec

def parse_file_to_record(path: str) -> Tuple[ParsedResume, str, str]:
    resume_text = extract_resume_text(path)
    # OCR not implemented here (placeholder)
    if needs_ocr(resume_text):
        # keep text as-is; in production call OCR here
        pass

    rid = str(uuid.uuid4())
    provider = get_provider()
    parsed_dict = provider.parse_resume(resume_id=rid, resume_text=resume_text, schema=json_schema())

    # Validate schema
    parsed = ParsedResume.model_validate(parsed_dict)

    # Ensure metadata exists
    md = parsed.metadata or {}
    md.setdefault("parsed_at", dt.datetime.utcnow().isoformat()+"Z")
    parsed.metadata = md

    return parsed, resume_text, rid
