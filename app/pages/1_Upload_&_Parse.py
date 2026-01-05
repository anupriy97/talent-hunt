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

import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import pandas as pd

from core.db import get_session, upsert_candidate
from core.config import project_root, resolve_db_url
from core.parser import parse_file_to_record, normalize_for_db

load_dotenv()

DATA_DIR = project_root() / "data" / "resumes"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_URL = resolve_db_url(os.getenv("DB_URL", "sqlite:///data/db/candidates.sqlite"))

st.set_page_config(page_title="Upload & Parse", layout="wide")
st.title("Upload & Parse Resumes")

st.write("Upload PDF/DOCX files. They will be stored locally and parsed into structured JSON.")

files = st.file_uploader("Upload resumes", type=["pdf", "docx"], accept_multiple_files=True)

show_debug = st.checkbox("Preview parsed JSON after parsing", value=False)

col1, col2 = st.columns([1,1])

if files and st.button("Parse uploaded files"):
    session = get_session(DB_URL)
    results = []
    for f in files:
        # Save file
        suffix = Path(f.name).suffix.lower()
        saved_name = f"{uuid.uuid4()}{suffix}"
        saved_path = DATA_DIR / saved_name
        with open(saved_path, "wb") as out:
            out.write(f.getbuffer())

        try:
            parsed, resume_text, rid = parse_file_to_record(str(saved_path))
            record = normalize_for_db(parsed, resume_text, source_filename=f.name)
            upsert_candidate(session, record)
            results.append({"source_filename": f.name, "resume_id": rid, "status": "parsed"})
        except Exception as e:
            results.append({"source_filename": f.name, "resume_id": None, "status": f"FAILED: {e}"})

    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True, hide_index=True)
    if show_debug:
        st.subheader("Parsed JSON (last successful)")
        # show last successful parsed json if any
        for item in reversed(results):
            if item.get("status") == "parsed":
                from core.db import get_candidate_json
                st.json(get_candidate_json(session, item["resume_id"]))
                break
    st.success("Done. Go to Search page to filter candidates.")

st.divider()
st.subheader("Tips")
st.markdown(
    """
- For a demo without any API keys, keep `LLM_PROVIDER=mock` in `.env`.
- To use a real LLM, set `LLM_PROVIDER=openai_compatible` and configure `LLM_API_BASE`, `LLM_API_KEY`, `LLM_MODEL`.
- Scanned PDFs may need OCR (placeholder in this assignment; add OCR in `core/extract.py`).
"""
)
