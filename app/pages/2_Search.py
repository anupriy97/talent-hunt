import sys
from pathlib import Path

def _ensure_project_root_on_path():
    here = Path(__file__).resolve()
    # Walk up until we find the project root containing 'core/'
    for p in [here] + list(here.parents):
        if (p / "core").exists():
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
            return

_ensure_project_root_on_path()

import os, json
from dotenv import load_dotenv
import streamlit as st
import pandas as pd

from core.db import get_session, query_candidates, get_candidate_json
from core.config import resolve_db_url
from core import taxonomy

load_dotenv()
DB_URL = resolve_db_url(os.getenv("DB_URL", "sqlite:///data/db/candidates.sqlite"))

st.set_page_config(page_title="Search Candidates", layout="wide")
st.title("Search & Filter Candidates")

session = get_session(DB_URL)

with st.sidebar:
    st.header("Filters")
    geo = st.multiselect("Geographic Market", taxonomy.GEOGRAPHIC_MARKETS)
    approach = st.multiselect("Approach", taxonomy.INVESTMENT_APPROACHES)
    sector = st.multiselect("Sector (any match)", taxonomy.SECTORS)
    role = st.multiselect("Role (any match)", taxonomy.ROLES)
    degree = st.multiselect("Degree level", taxonomy.DEGREE_LEVELS)
    min_exp, max_exp = st.slider("Years of Experience", 0, 30, (0, 30))
    include_unknown_exp = st.checkbox("Include candidates with unknown experience", value=True)
    keyword = st.text_input("Keyword (skills/employers/bullets)", value="")

records = query_candidates(
    session=session,
    geo_markets=geo or None,
    approaches=approach or None,
    sectors_any=sector or None,
    roles_any=role or None,
    degree_levels=degree or None,
    min_exp=float(min_exp),
    max_exp=float(max_exp),
    keyword=keyword or None,
    include_unknown_exp=include_unknown_exp,
    limit=500,
)

rows = []
for r in records:
    rows.append({
        "resume_id": r.resume_id,
        "name": r.full_name,
        "geo_market": r.geo_market,
        "country": r.country,
        "approach": r.approach,
        "years_experience": r.years_experience,
        "sectors": ", ".join(json.loads(r.sectors_json)),
        "top_programming": ", ".join(json.loads(r.skills_programming_json)[:3]),
        "source_filename": r.source_filename,
    })

df = pd.DataFrame(rows)

st.subheader(f"Results ({len(df)})")
st.dataframe(df, use_container_width=True, hide_index=True)

colA, colB, colC = st.columns([1,1,1])

with colA:
    st.download_button(
        "Export results CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="candidate_search_results.csv",
        mime="text/csv",
        disabled=df.empty
    )

with colB:
    selected_id = st.selectbox("Open candidate profile (resume_id)", df["resume_id"].tolist() if not df.empty else [])

with colC:
    show_evidence = st.checkbox("Show evidence snippets", value=True)

if selected_id:
    cand = get_candidate_json(session, selected_id)
    st.divider()
    st.subheader(cand.get("candidate", {}).get("full_name") or "Candidate Profile")

    left, right = st.columns([1,1])

    with left:
        st.markdown("### Summary")
        st.write(cand.get("summary", {}))

        st.markdown("### Target Fit")
        st.write(cand.get("target_fit", {}))

        st.markdown("### Skills")
        st.write(cand.get("skills", {}))

    with right:
        st.markdown("### Education")
        st.write(cand.get("education", []))

        st.markdown("### Experience")
        st.write(cand.get("experience", []))

    if show_evidence:
        st.markdown("### Evidence")
        st.json(cand.get("evidence", {}))
