# Goethe Parent Links

A single-page dashboard of school and community links for families at Goethe Elementary
(2236 N Rockwell St, Chicago — CPS school ID `609942`).

## Goal

Replace the "where was that link again" problem. One page, one tap to anything a parent
needs during the school year — lunch menu, absence form, grades portal, calendar, parent
Facebook groups. Shareable with family via a public URL.

## Scope decisions

- **Public, no personal info.** Nothing identifying — no student names, no household
  details. Everything on the page is either public CPS information or a link someone
  could already find. This is what makes a free-tier public GitHub Pages repo acceptable.
- **No accounts, no backend, no build step.** Static HTML in one file. It should still
  work if opened from a thumb drive in five years.
- **No browser storage.** Links live in a JS array in the source, not `localStorage`.
  Editing is a commit, which means version history and rollback — worth more here than
  in-page editing that only persists on one device.

## Technical decisions

| Decision | Why |
|---|---|
| Single self-contained `index.html` | No toolchain to maintain for ~25 links. Inline CSS/JS. |
| `LINKS` array as the config surface | One place to edit. `{ name, desc, url }` per link, grouped. |
| Direct MealViewer school URL | `schools.mealviewer.com/school/609942-51115` goes straight to Goethe's menu instead of the generic CPS meals page. |
| Client-side filter, `/` to focus | Faster than scanning 25 tiles on a phone. |
| Google Fonts via CDN | Bricolage Grotesque (display), Public Sans (body), IBM Plex Mono (data). Degrades to system fonts offline. |
| `noindex, nofollow` | Public but not searchable. Low-effort privacy floor. |

## Structure

```
index.html
├── <style>          design tokens in :root, then masthead / search / tiles
└── <script>
    ├── LINKS[]      ← the only thing that needs regular editing
    ├── render       builds sections from LINKS, no framework
    └── filter       input handler + "/" and Escape shortcuts
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

## Ideas not yet built

- Per-group "open all" (popup blockers make this fiddly).
- Dark mode.
- A second column of Logan Square community links — park district, library branch, soccer.
