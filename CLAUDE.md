# ManaBinder

A single-file web app (`index.html`, vanilla HTML/CSS/JS, no build step) for tracking a physical Magic: The Gathering collection as digital binders. It began as a copy of MegaBinder (Rob's Pokémon binder, `rstibal/megabinder`) and is now a separate code base. Version one deliberately copies MegaBinder's features and look; a friend of Rob's who collects Magic is testing it, and his feedback decides what comes next. Design: `docs/superpowers/specs/2026-11-14-manabinder-design.md`.

- Repo: `rstibal/manabinder`. Live site: https://rstibal.github.io/manabinder/ (GitHub Pages, deploys on push to `main`; the browser may cache the old page, so test with a `?v=N` query).
- Card data, pictures and prices: Scryfall (`https://api.scryfall.com`), English only.
- Storage: browser `localStorage` (`SK` = `mnBinder1` for binders). Cloud sync is optional and off until someone connects a GitHub token: it copies the whole state to a private gist using a classic token with only the `gist` scope. Without it, everything stays on the device.

## Rules for working here

- Rob reviews every change and says "push it" before anything is committed or pushed.
- Keep it one file with no dependencies unless asked.
- Bump `APP_VERSION` in `index.html` (format `YYYY.MM.DD.N`) with every change you push. It shows in the ☁ dialog so a device running a stale cached page can be spotted.
- Never ask for, enter or print a user's GitHub token.
- The file uses LF line endings (repo and working copy; `.gitattributes` says `eol=lf` and the repo sets `core.autocrlf false` locally). Preserve them when scripting edits.

## Living next to MegaBinder (same origin)

Both apps are served from `rstibal.github.io` (`/megabinder/` and `/manabinder/`), and browsers share `localStorage`, its ~5 MB quota, and Cache Storage across one origin. Losing Rob's Pokémon collection would be a failure even if ManaBinder works, so:

- Every `localStorage` key starts with `mn` (`mnBinder1`, `mnSets1`, `mnSync1`, `mnFit1`, `mnFx1`, and `mnBinder1.bak` before a sync pull). Never read or write a `pk…` key (MegaBinder's).
- Keep big caches out of `localStorage`: the quota is shared, and if ManaBinder filled it, MegaBinder's saves would start failing silently. Set listings (`fetchSetCards`) and card records (`cardDetailCache`) are kept in memory only, for the session.
- Do not rename `GIST_DESC` / `GIST_FILE` (`manabinder data (do not edit)` / `manabinder.json`): sync finds the existing gist by those names, and they keep it apart from MegaBinder's `pokemon-binder` gist when one GitHub account is used for both. Never touch that gist. Don't rename `localStorage` keys without a migration.
- Service worker caches are `manabinder-app-v1` and `manabinder-img-v1`, and `activate` deletes only old caches whose names start with `manabinder-` (MegaBinder's worker does the same for `megabinder-`). The worker is registered from this folder, so its scope stays `/manabinder/`.
- Share links use the app's own URL.

## Scryfall

- At most about 10 requests a second: every call goes through `sf()`, which starts requests at least 100 ms apart and retries 429/5xx. Send `Accept: application/json` (browsers can't set a User-Agent; that's fine).
- Bulk work goes through `/cards/search` (175 cards a page, `sfAll()` follows `next_page`) and `/cards/collection` (75 ids per POST, `fetchDetails()`), never one request per card. One malformed id makes Scryfall refuse a whole collection batch, so ids are checked against `UUID` first.
- Card search: `/cards/autocomplete` offers names; the chosen or typed name goes to `/cards/named?fuzzy=`, then every printing is fetched by `oracleid:` (so names with quotes and punctuation work), newest first. All searches add `game:paper`, `unique=prints`, `include_extras`, `include_variations`.
- Sets come from `/sets`, cached a week (`mnSets1`). Left out: digital-only sets and the types `token`, `memorabilia` (art series, front cards), `minigame`, `alchemy`, `treasure_chest`, plus sets with no cards. Promos and Secret Lair stay.
- Use Scryfall's image URLs directly (`cards.scryfall.io`); don't copy or re-host pictures. The app must stay free (Scryfall requires that its data not be paywalled).
- Prices: TCGplayer USD from Scryfall by finish (`usd`, `usd_foil`, `usd_etched`). With no USD price, Cardmarket EUR (`eur`, `eur_foil`; there is no etched EUR) converted with frankfurter.dev's daily rate and marked ≈. The buy link is `purchase_uris.tcgplayer`. Scryfall updates prices about once a day.

## Cards

- A slot holds `{ id, scryfallId, name, set, setId, number, rarity, finish, typeLine, imageSmall, imageLarge, imageBack?, imageBackLarge?, owned?, addedAt }`. `owned: false` means "need" (planned, shown greyed out). `imageSmall` is Scryfall's `normal` size (488 px; their `small` blurs in a binder slot), `imageLarge` is `large`; the add dialogs show `small` thumbnails.
- Finish is automatic from the printing's Scryfall `finishes`: `nonfoil` (shown as "Normal"), `foil`, `etched`. A printing with more than one finish offers them as separate choices when adding (finish buttons in the add dialog; the "Foil" row in bulk add). There is no other manual finish picker, so don't add one.
- Double-faced cards are the ones with no top-level `image_uris` and a picture per face (transform, modal double-faced, reversible, battles). The slot shows the front; the popup's flip button shows the back. Split, adventure, flip and meld cards have one picture and no flip button.
- Landscape pictures (planes, some battles) show whole in the upright slot (`imgLand()` adds class `land`, `object-fit: contain`), not rotated.
- Share links (`#share=…`, format v2) carry only Scryfall id, finish code and need flag per slot plus the layout; the viewer looks the cards up through `/cards/collection`.

## Look and behaviour

- Dark layout from MegaBinder with a violet accent (`--acc` `#8b5cf6`). The emblem is an original faceted gem in a dark ring (not a mana symbol, and no Wizards of the Coast logos or the Magic name as branding), drawn inline in the header and rail SVGs and by `python tools/build_icons.py` for the home-screen icons (keep it inside the central 80% so Android's maskable crop doesn't cut it). Change all three together.
- Keep visual effects subtle and non-animated; Rob finds motion distracting. Foil is static stripes and a pale frame, Etched a static silver-and-gold frame. The one allowed motion is the quick (~180 ms) slide when the page turns.
- The app is an installable PWA: `manifest.webmanifest`, `sw.js` and the `icon-*.png` / `apple-touch-icon.png` files sit beside `index.html`. Keep the service worker network-first for the app (cache-first would bring back the stale-page problem) and add any new top-level asset to its `SHELL` list.
- Navigation: `layout()` runs on every resize and sets body classes. At 900px and up (not in fit mode) it is the labelled sidebar. Below that, and always in fit mode, it is the icon rail (`#rail`, extra items in the `#rmenu` menu): `nav-c` compact, `nav-bar` rail across the top (narrow screens), `nav-s` tighter buttons. Fit to screen (`toggleFit()`) sizes the cards so the whole page fits the window, keeping the 2.5:3.5 ratio; it is saved per device (`mnFit1`), not synced. The emblem must show at every size, orientation and zoom, including the Galaxy Z Fold4 opened and folded (Rob's main device). Swiping left/right turns the page (not while rearranging). When changing layout, check that nothing scrolls sideways and the rail doesn't overflow.
- Drag-and-drop for slots is behind the "Layout locked" toggle; free drag-and-drop is deferred. Don't build it unless asked.

## Checking changes

Serve locally on a port MegaBinder doesn't use, so the two apps' test data stay apart (`python -m http.server 8766`), and open `http://localhost:8766/`. Seed a binder in the console by setting `st` and calling `renderAll()`, or use the add dialogs. Check desktop (sidebar layout, 900px and up), phone width (rail across the top), the Fold4 folded (~344px) and open (~690px), and fit mode. Afterwards unregister the service worker, delete the `manabinder-` caches and clear the test origin's storage.
