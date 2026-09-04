#!/usr/bin/env python3
"""Bake the prep-class rotation into index.html.

The schedule is fixed for the school year, so the page carries it inline
rather than fetching a fourth file for one small pill at the top. The source
JSON is kept locally and stays out of this repo (see .gitignore) — only the
baked table ships. Rerun this when a new year's schedule lands:

    python3 tools/build-prep.py goethe_k106_prep_schedule_2026_2027.json

It rewrites the block between the PREP_DAYS markers in index.html.
"""
import json, re, sys
from pathlib import Path

LETTER = {"Music": "M", "P.E.": "P", "Library": "L"}
SRC = Path(sys.argv[1] if len(sys.argv) > 1
           else "goethe_k106_prep_schedule_2026_2027.json")
PAGE = Path(__file__).resolve().parent.parent / "index.html"

months = {}
for row in json.loads(SRC.read_text()):
    if row["school_day"] != "TRUE":
        continue
    letter = LETTER.get(row["prep_class"])
    if not letter:
        sys.exit(f"unknown prep class {row['prep_class']!r} on {row['date']}")
    month, day = row["date"][:7], row["date"][8:]
    months.setdefault(month, []).append(f"{int(day)}{letter}")

body = "\n".join(f'  "{m}": "{" ".join(d)}",' for m, d in months.items())
block = f"const PREP_DAYS = {{\n{body}\n}};"

page = PAGE.read_text()
new = re.sub(r"(/\* PREP_DAYS start \*/\n).*?(\n/\* PREP_DAYS end \*/)",
             lambda m: m.group(1) + block + m.group(2), page, flags=re.S)
if new == page:
    sys.exit("markers not found (or nothing changed) in index.html")
PAGE.write_text(new)
print(f"{sum(len(d) for d in months.values())} school days, "
      f"{months and min(months)} – {months and max(months)}")
