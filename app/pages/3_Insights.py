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
import matplotlib.pyplot as plt

from core.db import get_session, query_candidates
from core.config import resolve_db_url
from core import taxonomy

load_dotenv()
DB_URL = resolve_db_url(os.getenv("DB_URL", "sqlite:///data/db/candidates.sqlite"))

st.set_page_config(page_title="Insights", layout="wide")
st.title("Candidate Pool Insights")

session = get_session(DB_URL)
records = query_candidates(session=session, limit=5000)

if not records:
    st.warning("No candidates yet. Upload and parse resumes first.")
    st.stop()

# Build dataframe
rows=[]
for r in records:
    sectors = json.loads(r.sectors_json)
    for s in sectors or ["(None)"]:
        rows.append({
            "resume_id": r.resume_id,
            "geo_market": r.geo_market or "(Unknown)",
            "approach": r.approach or "(Unknown)",
            "sector": s or "(None)",
            "years_experience": r.years_experience,
        })

df = pd.DataFrame(rows)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Candidates", len(set(df["resume_id"])))

with c2:
    st.metric("Geo markets", df["geo_market"].nunique())

with c3:
    st.metric("Sectors (incl none)", df["sector"].nunique())

st.divider()

# Distribution by geo
st.subheader("Distribution by Geographic Market")
geo_counts = df.drop_duplicates("resume_id")["geo_market"].value_counts()

fig = plt.figure()
geo_counts.plot(kind="bar")
plt.xlabel("Geo market")
plt.ylabel("Candidates")
st.pyplot(fig, clear_figure=True)

# Distribution by approach
st.subheader("Distribution by Approach")
ap_counts = df.drop_duplicates("resume_id")["approach"].value_counts()
fig = plt.figure()
ap_counts.plot(kind="bar")
plt.xlabel("Approach")
plt.ylabel("Candidates")
st.pyplot(fig, clear_figure=True)

# Sector counts
st.subheader("Distribution by Sector (any exposure)")
sector_counts = df["sector"].value_counts().head(15)
fig = plt.figure()
sector_counts.plot(kind="bar")
plt.xlabel("Sector")
plt.ylabel("Mentions")
st.pyplot(fig, clear_figure=True)

# Experience histogram
st.subheader("Years of Experience Histogram")
exp = df.drop_duplicates("resume_id")["years_experience"].dropna()
fig = plt.figure()
plt.hist(exp, bins=15)
plt.xlabel("Years of experience")
plt.ylabel("Candidates")
st.pyplot(fig, clear_figure=True)
