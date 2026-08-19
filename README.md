# Goethe Parent Links

A single-page dashboard of school and community links for families at Goethe Elementary
(2236 N Rockwell St, Chicago — CPS school ID `609942`).

## Goal

Replace the "where was that link again" problem. One page, one tap to anything a parent
needs during the school year — absence form, grades portal, calendar, parent Facebook
groups. The day's school meals and the week's school events are shown on the page itself
rather than linked out to.
Shareable with family via a public URL.

## Scope decisions

- **Public, no personal info.** Nothing identifying — no student names, no household
  details. Everything on the page is either public CPS information or a link someone
  could already find. This is what makes a free-tier public GitHub Pages repo acceptable.
- **No accounts, no backend.** Static HTML in one file. It should still work if opened
  from a thumb drive in five years — meals and calendar events are the two parts that
  need the network, and each degrades to a "couldn't load, here's the link" fallback.
- **One scheduled job, no build step.** Nothing compiles the page; editing is still just
  editing `index.html`. A nightly Action refreshes `events.json` because Google gives us
  no way to read the calendars from the browser (below).
- **No browser storage.** Links live in a JS array in the source, not `localStorage`.
  Editing is a commit, which means version history and rollback — worth more here than
  in-page editing that only persists on one device.

## Technical decisions

| Decision | Why |
|---|---|
| Single self-contained `index.html` | No toolchain to maintain for ~25 links. Inline CSS/JS. |
| `LINKS` array as the config surface | One place to edit. `{ name, desc, url }` per link, grouped. |
| Meals fetched live from MealViewer | `api.mealviewer.com` serves `Access-Control-Allow-Origin: *`, so the browser can read it straight from GitHub Pages — no proxy, no scheduled job, no menu data committed to the repo. |
| Calendar events baked into `events.json` | Google's public `.ics` feeds send **no** `Access-Control-Allow-Origin`, so the browser can't read them the way it reads MealViewer. Rejected: a CORS proxy (a third-party dependency on a page meant to outlast it) and the Calendar API v3, which *is* CORS-enabled but wants a Google Cloud project and a browser API key living in a public repo. A nightly Action costs no accounts and no key. |
| `icalendar` + `recurring-ical-events` in the job | The feeds carry 170 `RRULE`s, 276 `RECURRENCE-ID` overrides and 249 `EXDATE`s. Expanding that by hand is a correctness trap; these libraries do it, including the timezone math. |
| The job rewrites `events.json` only when events move | Its window slides daily, so a naive run would commit every night forever. It compares the event list and leaves the file alone otherwise, keeping the history meaningful. |
| Whole week, Monday–Sunday | Saturday is a real school-sports day, so a Mon–Fri week (what meals use) would hide games. Multi-day events repeat on each day they cover — on Wednesday you want to see that it's still spring break. |
| Empty week falls back to "Next up" | Most of summer has nothing scheduled. A blank card tells a parent nothing; the next dated thing does. |
| One day by default, week on click | The day's card costs ~34KB gzipped; the whole week is ~150KB. Most visits only want today, so the week is fetched lazily on the first click and cached — toggling after that is free. |
| K-8 breakfast + lunch only | The API returns five blocks per day (Pre-K and snacks too); showing all of them buried the links. On weekends the page rolls forward to the coming Monday and says so. |
| All-caps items are section headers | MealViewer stores `FEATURED ENTREES` / `AVAILABLE DAILY` / `CHOICE OF MILK` as ordinary food items. Real food always has lowercase letters — checked against 7 months of menus (15 all-caps strings, all headers; 3,017 real items). `portionUnit: "DONT USE"` looks like the same signal but is unreliable. |
| Client-side filter, `/` to focus | Faster than scanning 25 tiles on a phone. |
| Google Fonts via CDN | Bricolage Grotesque (display), Public Sans (body), IBM Plex Mono (data). Degrades to system fonts offline. |
| `noindex, nofollow` | Public but not searchable. Low-effort privacy floor. |

## Structure

```
index.html
├── <style>          design tokens in :root, then masthead / search / tiles / meals / week
└── <script>
    ├── LINKS[]      ← the only thing that needs regular editing
    ├── render       builds sections from LINKS, no framework
    ├── filter       input handler + "/" and Escape shortcuts (meals and week match too)
    ├── meals        day math (Chicago time) → fetch → parse → render
    │                one card, or five behind the toggle
    └── week         fetch events.json → bucket into Mon–Sun → render
                     falls back to the next dated event when the week is empty

events.json                     generated; don't hand-edit
tools/build-events.py           the generator — runnable locally
.github/workflows/events.yml    runs it nightly at 4:15am Chicago
```

## The calendar job

Three Google Calendars feed it — Goethe Community, SCORE! Sports, and Out of School Time.
US Holidays is deliberately left out: it duplicates the CPS calendar already linked on the
page. IDs live at the top of `tools/build-events.py`.

The job keeps a rolling window (7 days back, 120 forward) so the page can still name the
next event when the current week is empty, and so a missed run or two goes unnoticed. If
any feed fails it exits without writing, leaving the last good `events.json` in place
rather than silently publishing a calendar with a third of its events missing.

To run it by hand:

```bash
pip install icalendar recurring-ical-events
python3 tools/build-events.py
```

## Hosting

GitHub Pages, free personal account.

```bash
git init -b main
git add . && git commit -m "Goethe parent links dashboard"
gh repo create goethe-links --public --source=. --push
```

Then Settings → Pages → Deploy from a branch → `main` / `/ (root)`.
Live at `<username>.github.io/goethe-links/`. Pushes rebuild in ~30s.

Rejected alternatives: Google Drive (dropped static hosting in 2016), Google Sites
(embed code size cap), Netlify Drop and Cloudflare Pages (both fine, but GitHub wins on
edit history given the repo is already local).

## Open items

- Verify the Aspen link. Currently points at the CPS portal landing page rather than the
  login itself, which was the safer choice but adds a click.
- Consider a `404.html`.
- CPS reorganizes its site periodically. Links are worth a check each August.
- The meals block depends on an undocumented MealViewer API. If it ever changes shape the
  page falls back to a link, but the parsing would need revisiting.
- Condiments are filtered by name (`CONDIMENT` in the script). New ones will slip through
  until added.
- While collapsed, the filter box only searches the day on screen — a term matching
  Friday's lunch finds nothing until the week is expanded.
- The Out of School Time calendar has nothing scheduled past June 2026. If it stays empty
  into the school year, drop it from `CALENDARS`.
- Nothing warns us if the nightly job starts failing except the page's own "last synced"
  line, which only appears after a week of silence.

## Ideas not yet built

- Per-group "open all" (popup blockers make this fiddly).
- Dark mode.
- A second column of Logan Square community links — park district, library branch, soccer.
