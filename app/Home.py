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
from dotenv import load_dotenv
import streamlit as st
from core.config import resolve_db_url

load_dotenv()

st.set_page_config(page_title="Millennium BD Resume Platform", layout="wide")

st.title("Millennium BD Resume Search Platform")
st.write(
    """
Use the left sidebar to navigate:
- **Upload & Parse**: upload PDF/DOCX resumes and parse into structured JSON
- **Search**: filter candidates by geo/approach/sector/skills/experience + keyword search
- **Insights**: visualize candidate pool distributions
"""
)

st.info(f"LLM_PROVIDER = `{os.getenv('LLM_PROVIDER','mock')}` | DB_URL = `{resolve_db_url(os.getenv('DB_URL','sqlite:///data/db/candidates.sqlite'))}`")
