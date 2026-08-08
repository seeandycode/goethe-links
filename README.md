# Goethe Parent Links

A single-page dashboard of school and community links for families at Goethe Elementary
(2236 N Rockwell St, Chicago — CPS school ID `609942`).

## Goal

Replace the "where was that link again" problem. One page, one tap to anything a parent
needs during the school year — absence form, grades portal, calendar, parent Facebook
groups. The day's school meals are shown on the page itself rather than linked out to.
Shareable with family via a public URL.

## Scope decisions

- **Public, no personal info.** Nothing identifying — no student names, no household
  details. Everything on the page is either public CPS information or a link someone
  could already find. This is what makes a free-tier public GitHub Pages repo acceptable.
- **No accounts, no backend, no build step.** Static HTML in one file. It should still
  work if opened from a thumb drive in five years — the meals block is the one part that
  needs the network, and it degrades to a "couldn't load, open MealViewer" link.
- **No browser storage.** Links live in a JS array in the source, not `localStorage`.
  Editing is a commit, which means version history and rollback — worth more here than
  in-page editing that only persists on one device.

## Technical decisions

| Decision | Why |
|---|---|
| Single self-contained `index.html` | No toolchain to maintain for ~25 links. Inline CSS/JS. |
| `LINKS` array as the config surface | One place to edit. `{ name, desc, url }` per link, grouped. |
| Meals fetched live from MealViewer | `api.mealviewer.com` serves `Access-Control-Allow-Origin: *`, so the browser can read it straight from GitHub Pages — no proxy, no scheduled job, no menu data committed to the repo. |
| One day by default, week on click | The day's card costs ~34KB gzipped; the whole week is ~150KB. Most visits only want today, so the week is fetched lazily on the first click and cached — toggling after that is free. |
| K-8 breakfast + lunch only | The API returns five blocks per day (Pre-K and snacks too); showing all of them buried the links. On weekends the page rolls forward to the coming Monday and says so. |
| All-caps items are section headers | MealViewer stores `FEATURED ENTREES` / `AVAILABLE DAILY` / `CHOICE OF MILK` as ordinary food items. Real food always has lowercase letters — checked against 7 months of menus (15 all-caps strings, all headers; 3,017 real items). `portionUnit: "DONT USE"` looks like the same signal but is unreliable. |
| Client-side filter, `/` to focus | Faster than scanning 25 tiles on a phone. |
| Google Fonts via CDN | Bricolage Grotesque (display), Public Sans (body), IBM Plex Mono (data). Degrades to system fonts offline. |
| `noindex, nofollow` | Public but not searchable. Low-effort privacy floor. |

## Structure

```
index.html
├── <style>          design tokens in :root, then masthead / search / tiles / meals
└── <script>
    ├── LINKS[]      ← the only thing that needs regular editing
    ├── render       builds sections from LINKS, no framework
    ├── filter       input handler + "/" and Escape shortcuts (meals match too)
    └── meals        day math (Chicago time) → fetch → parse → render
                     one card, or five behind the toggle
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

## Ideas not yet built

- Per-group "open all" (popup blockers make this fiddly).
- Dark mode.
- A second column of Logan Square community links — park district, library branch, soccer.
