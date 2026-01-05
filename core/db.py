from __future__ import annotations
import json
from .config import resolve_db_url
from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, Column, String, Float, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import text as sql_text

Base = declarative_base()

class CandidateRecord(Base):
    __tablename__ = "candidates"

    resume_id = Column(String, primary_key=True)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    geo_market = Column(String, nullable=True)      # US/Europe/APAC
    country = Column(String, nullable=True)
    approach = Column(String, nullable=True)        # Fundamental/Systematic

    years_experience = Column(Float, nullable=True)
    degree_level = Column(String, nullable=True)

    sectors_json = Column(Text, nullable=False, default="[]")
    asset_classes_json = Column(Text, nullable=False, default="[]")
    roles_json = Column(Text, nullable=False, default="[]")

    skills_programming_json = Column(Text, nullable=False, default="[]")
    skills_data_json = Column(Text, nullable=False, default="[]")
    skills_ml_json = Column(Text, nullable=False, default="[]")
    skills_finance_json = Column(Text, nullable=False, default="[]")
    skills_tools_json = Column(Text, nullable=False, default="[]")

    # For keyword search (employers, titles, bullets, skills)
    search_blob = Column(Text, nullable=False, default="")

    # Canonical structured JSON (entire LLM parse)
    parsed_json = Column(Text, nullable=False)

    # Source file reference
    source_filename = Column(String, nullable=True)

def get_engine(db_url: str):
    db_url = resolve_db_url(db_url)
    return create_engine(db_url, future=True)

def init_db(db_url: str):
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    return engine

def get_session(db_url: str):
    db_url = resolve_db_url(db_url)
    engine = init_db(db_url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()

def _to_json_str(x: Any) -> str:
    return json.dumps(x or [], ensure_ascii=False)

def upsert_candidate(session, record: Dict[str, Any]) -> None:
    """
    record: dict with keys matching CandidateRecord columns.
    """
    existing = session.get(CandidateRecord, record["resume_id"])
    if existing:
        for k, v in record.items():
            setattr(existing, k, v)
    else:
        session.add(CandidateRecord(**record))
    session.commit()

def query_candidates(
    session,
    geo_markets: List[str] | None = None,
    countries: List[str] | None = None,
    approaches: List[str] | None = None,
    sectors_any: List[str] | None = None,
    roles_any: List[str] | None = None,
    min_exp: float | None = None,
    max_exp: float | None = None,
    degree_levels: List[str] | None = None,
    keyword: str | None = None,
    include_unknown_exp: bool = True,
    limit: int = 500,
) -> List[CandidateRecord]:
    q = session.query(CandidateRecord)

    if geo_markets:
        q = q.filter(CandidateRecord.geo_market.in_(geo_markets))
    if countries:
        q = q.filter(CandidateRecord.country.in_(countries))
    if approaches:
        q = q.filter(CandidateRecord.approach.in_(approaches))
    if degree_levels:
        q = q.filter(CandidateRecord.degree_level.in_(degree_levels))
    # Experience range filtering:
    # By default we keep candidates with unknown years_experience (NULL) in results.
    # If include_unknown_exp=False, we restrict to only those with a numeric value.
    if min_exp is not None or max_exp is not None:
        if include_unknown_exp:
            from sqlalchemy import or_, and_
            conds = []
            if min_exp is not None and max_exp is not None:
                conds.append(and_(CandidateRecord.years_experience.isnot(None),
                                  CandidateRecord.years_experience >= min_exp,
                                  CandidateRecord.years_experience <= max_exp))
            elif min_exp is not None:
                conds.append(and_(CandidateRecord.years_experience.isnot(None),
                                  CandidateRecord.years_experience >= min_exp))
            elif max_exp is not None:
                conds.append(and_(CandidateRecord.years_experience.isnot(None),
                                  CandidateRecord.years_experience <= max_exp))
            q = q.filter(or_(CandidateRecord.years_experience.is_(None), *conds))
        else:
            if min_exp is not None:
                q = q.filter(CandidateRecord.years_experience.isnot(None)).filter(CandidateRecord.years_experience >= min_exp)
            if max_exp is not None:
                q = q.filter(CandidateRecord.years_experience.isnot(None)).filter(CandidateRecord.years_experience <= max_exp)

    # Sectors/Roles (simple contains search on JSON string)
    # For large scale, move to OpenSearch or a normalized join table.
    if sectors_any:
        conds = []
        for s in sectors_any:
            conds.append(CandidateRecord.sectors_json.like(f'%"{s}"%'))
        q = q.filter(sql_text(" OR ".join([f"sectors_json LIKE :s{i}" for i,_ in enumerate(conds)]))).params(**{f"s{i}": f'%"{s}"%' for i,s in enumerate(sectors_any)})

    if roles_any:
        q = q.filter(sql_text(" OR ".join([f"roles_json LIKE :r{i}" for i in range(len(roles_any))]))).params(**{f"r{i}": f'%"{r}"%' for i,r in enumerate(roles_any)})

    if keyword:
        kw = keyword.strip().lower()
        q = q.filter(CandidateRecord.search_blob.like(f"%{kw}%"))

    return q.order_by(CandidateRecord.years_experience.desc().nullslast()).limit(limit).all()

def get_candidate_json(session, resume_id: str) -> Dict[str, Any]:
    rec = session.get(CandidateRecord, resume_id)
    if not rec:
        raise KeyError(resume_id)
    return json.loads(rec.parsed_json)
