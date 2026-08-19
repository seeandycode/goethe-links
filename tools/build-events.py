#!/usr/bin/env python3
"""Bake the school's Google Calendars into events.json.

Google's public .ics endpoints send no Access-Control-Allow-Origin, so the page
cannot read them from the browser the way it reads MealViewer. A scheduled job
fetches them here instead and commits a small JSON file the page loads
same-origin. See .github/workflows/events.yml.

Run locally with:  python3 tools/build-events.py
"""

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import icalendar
import recurring_ical_events

# The four feeds embedded on the school's Sites calendar page, minus US
# Holidays (already on the CPS calendar we link to, and not school news).
CALENDARS = [
    ("community", "cps.edu_sve4jok0abnj3olaul5qdttfvo@group.calendar.google.com"),
    ("sports",    "c_mdt5q40nlhhs6doc9skm8oimbk@group.calendar.google.com"),
    ("ost",       "c_mo3uhgo5r41hlkinpsdod7tjg8@group.calendar.google.com"),
]

CHICAGO = ZoneInfo("America/Chicago")

# Enough runway that an empty week can still name the next thing coming up,
# and that a missed run or two goes unnoticed.
DAYS_BACK = 7
DAYS_AHEAD = 120

OUT = "events.json"


def ics_url(cal_id):
    quoted = urllib.parse.quote(cal_id, safe="")
    return f"https://calendar.google.com/calendar/ical/{quoted}/public/basic.ics"


def fetch(cal_id):
    req = urllib.request.Request(ics_url(cal_id), headers={"User-Agent": "goethe-links"})
    with urllib.request.urlopen(req, timeout=60) as r:
        if r.status != 200:
            raise RuntimeError(f"HTTP {r.status}")
        return r.read()


def local_parts(value):
    """An ical date/datetime -> (YYYY-MM-DD, "HH:MM" or None) in Chicago."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=CHICAGO)
        local = value.astimezone(CHICAGO)
        return local.date().isoformat(), local.strftime("%H:%M")
    return value.isoformat(), None


# City/state/country tails carry no information for a Chicago school.
BOILERPLATE = re.compile(r"^(usa|us|chicago|il|illinois|[A-Z]{2}\s*\d{5}(-\d{4})?|\d{5})$", re.I)


def venue(location):
    """Google stores full postal addresses. In a narrow column the venue name
    is the only part worth the line: "Riis Park, 6100 W Fullerton Ave, Chicago,
    IL 60639, USA" -> "Riis Park"."""
    parts = [p.strip() for p in location.split(",") if p.strip()]
    while parts and BOILERPLATE.match(parts[-1]):
        parts.pop()
    # A street address after the venue name is noise too; the name alone locates it.
    if len(parts) > 1 and re.match(r"^\d", parts[1]):
        parts = parts[:1]
    return ", ".join(parts)[:60]


def collect(key, raw, window_start, window_end):
    cal = icalendar.Calendar.from_ical(raw)
    events = []
    for ev in recurring_ical_events.of(cal).between(window_start, window_end):
        summary = str(ev.get("SUMMARY", "")).strip()
        if not summary:
            continue
        if str(ev.get("STATUS", "")).upper() == "CANCELLED":
            continue

        start_day, start_time = local_parts(ev["DTSTART"].dt)
        out = {"c": key, "d": start_day, "s": summary}
        if start_time:
            out["t"] = start_time

        # Only all-day spans need an end date; the page shows start times but
        # never end times, so a timed event's DTEND is dropped.
        if "DTEND" in ev and not start_time:
            end_day, _ = local_parts(ev["DTEND"].dt)
            # An all-day DTEND is exclusive: Mon-Tue spans through Monday.
            last = date.fromisoformat(end_day) - timedelta(days=1)
            if last.isoformat() > start_day:
                out["e"] = last.isoformat()

        location = venue(str(ev.get("LOCATION", "")).strip())
        if location:
            out["l"] = location

        events.append(out)
    return events


def main():
    today = datetime.now(CHICAGO).date()
    window_start = datetime.combine(today - timedelta(days=DAYS_BACK), time.min, CHICAGO)
    window_end = datetime.combine(today + timedelta(days=DAYS_AHEAD), time.max, CHICAGO)

    events = []
    for key, cal_id in CALENDARS:
        try:
            events += collect(key, fetch(cal_id), window_start, window_end)
        except Exception as exc:
            # Bail rather than commit a file that silently lost a calendar —
            # the last good events.json stays in place.
            sys.exit(f"{key}: {exc}")

    events.sort(key=lambda e: (e["d"], e.get("t", "00:00"), e["s"]))

    # The window slides every day, so "generated" alone would churn a commit
    # each night. Only rewrite when the events themselves moved.
    try:
        with open(OUT, encoding="utf-8") as f:
            if json.load(f).get("events") == events:
                print(f"{len(events)} events, unchanged")
                return
    except (OSError, ValueError):
        pass

    payload = {
        "generated": datetime.now(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "through": (today + timedelta(days=DAYS_AHEAD)).isoformat(),
        "events": events,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=0, sort_keys=False)
        f.write("\n")
    print(f"{len(events)} events -> {OUT}")


if __name__ == "__main__":
    main()
