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
import argparse
import pandas as pd
from dotenv import load_dotenv
from core.db import get_session, query_candidates, get_candidate_json

def main():
    load_dotenv()
    db_url = os.getenv("DB_URL", "sqlite:///data/db/candidates.sqlite")
    session = get_session(db_url)

    ap = argparse.ArgumentParser()
    ap.add_argument("--out_csv", default="all_candidates.csv")
    ap.add_argument("--out_jsonl", default="all_candidates.jsonl")
    args = ap.parse_args()

    recs = query_candidates(session=session, limit=100000)
    rows=[]
    with open(args.out_jsonl, "w", encoding="utf-8") as f:
        for r in recs:
            cand = get_candidate_json(session, r.resume_id)
            f.write(json.dumps(cand, ensure_ascii=False) + "\n")
            rows.append({
                "resume_id": r.resume_id,
                "name": r.full_name,
                "geo_market": r.geo_market,
                "approach": r.approach,
                "years_experience": r.years_experience,
                "source_filename": r.source_filename,
            })
    pd.DataFrame(rows).to_csv(args.out_csv, index=False)
    print(f"Wrote {args.out_csv} and {args.out_jsonl}")

if __name__ == "__main__":
    main()
