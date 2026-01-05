import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

from core.db import get_session, upsert_candidate
from core.parser import parse_file_to_record, normalize_for_db

def main():
    load_dotenv()
    db_url = os.getenv("DB_URL", "sqlite:///data/db/candidates.sqlite")
    session = get_session(db_url)

    ap = argparse.ArgumentParser()
    ap.add_argument("--input_dir", required=True, help="Directory with PDF/DOCX resumes")
    args = ap.parse_args()

    inp = Path(args.input_dir)
    files = list(inp.glob("*.pdf")) + list(inp.glob("*.docx"))
    if not files:
        print("No PDF/DOCX found.")
        return

    for f in files:
        try:
            parsed, resume_text, rid = parse_file_to_record(str(f))
            record = normalize_for_db(parsed, resume_text, source_filename=f.name)
            upsert_candidate(session, record)
            print(f"Parsed: {f.name} -> {rid}")
        except Exception as e:
            print(f"FAILED: {f.name}: {e}")

if __name__ == "__main__":
    main()
