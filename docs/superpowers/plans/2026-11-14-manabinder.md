# ManaBinder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Magic: The Gathering copy of MegaBinder (binders of card pages, planner, prices, share links, optional gist sync) fed by Scryfall, living safely beside MegaBinder on `rstibal.github.io`.

**Architecture:** Start from a byte copy of MegaBinder's `index.html`, `sw.js`, `manifest.webmanifest`, `tools/build_icons.py`, `.gitignore`. Strip the Pokémon-only code paths (languages, gap data, stand-in art, TCGdex image fallbacks, rarity-based finishes, art upgrade), rename every storage key / gist name / cache, then replace the TCGdex layer (sets, search, set listing, card details, prices) with a Scryfall layer that keeps the same function roles so the UI code above it barely changes.

**Tech Stack:** One `index.html` (vanilla HTML/CSS/JS, no build, no libraries), a network-first service worker, Python + Pillow for the icon script. Scryfall REST API; GitHub Gists API for optional sync; frankfurter.dev for EUR→USD.

**Spec:** `docs/superpowers/specs/2026-11-14-manabinder-design.md`

## Global Constraints

- Every `localStorage` key starts with `mn` (`mnBinder1`, `mnSets1`, `mnSync1`, `mnFit1`, `mnFx1`). The ~5 MB quota is shared with MegaBinder, so set listings are cached in memory only, never in `localStorage`. No `pk…` key is read or written anywhere, including `.bak` copies.
- Gist description `manabinder data (do not edit)`, gist file `manabinder.json`.
- Service worker caches `manabinder-app-v1` and `manabinder-img-v1`; `activate` deletes only caches whose names start with `manabinder-`. Worker registered as `sw.js` from the app folder (scope `/manabinder/`).
- Scryfall: at most ~10 requests/s (one shared queue, ≥100 ms between request starts), `Accept: application/json`, bulk lookups through `/cards/search` (175/page) and `/cards/collection` (≤75 ids per POST). Image URLs used directly from `cards.scryfall.io`.
- English only; USD prices (`usd`, `usd_foil`, `usd_etched` by finish); EUR (`eur`, `eur_foil`) converted and marked ≈ only when USD is missing; buy link `purchase_uris.tcgplayer`.
- Finish is automatic from Scryfall `finishes` (`nonfoil` → "Normal", `foil` → "Foil", `etched` → "Etched"). No manual finish picker beyond choosing among the finishes a printing actually has.
- No animation except the existing ~180 ms page-turn slide (the spinner keeps spinning; MegaBinder's animated holo shimmer is not carried over).
- `APP_VERSION` format `YYYY.MM.DD.N`, starting `2026.11.14.1`.
- LF line endings; `git config core.autocrlf false` in the new repo.
- Excluded sets: `digital: true`, and `set_type` in `token`, `memorabilia` (art series, front cards…), `minigame`, `alchemy`, `treasure_chest`; also sets with `card_count` 0. Everything else (promos, Secret Lair, commander, planechase, archenemy, vanguard, funny) is kept.
- Nothing is committed or pushed, and no GitHub repo or Pages is created, until Rob says "push it". Never ask for, enter or print a GitHub token.

## Decisions the spec left to the builder

- **Card record** (one slot): `{ id, scryfallId, name, set, setId, number, rarity, finish, layout?, imageSmall, imageLarge, imageBack?, imageBackLarge?, typeLine?, owned?, addedAt }`. `finish` replaces MegaBinder's `variant` and holds Scryfall's own words (`nonfoil` / `foil` / `etched`). `imageSmall` is Scryfall's `normal` size (488 px: `small` is 146 px and blurs in a 3×3 page), `imageLarge` is `large`. Add-dialog thumbnails use the `small` size, derived by swapping the `/normal/` path segment.
- **Double-faced** = the card has no top-level `image_uris` and `card_faces[1].image_uris` exists (transform, modal_dfc, reversible_card, battles, double-faced tokens). Meld cards have one picture on Scryfall and get no flip button.
- **Landscape** pictures (planes, battles): on image load, if `naturalWidth > naturalHeight` the img gets class `land` (`object-fit: contain` on the slot background). No rotation.
- **Printing picker**: the existing add dialog. The name box shows a Scryfall autocomplete dropdown (`/cards/autocomplete`); picking a name (or Enter) lists its printings newest first, one tile per printing with set code + number. Selecting a tile shows the existing selection panel; when the printing has more than one finish, finish buttons (the existing `.vopts` style) appear in it, defaulting to the first of nonfoil/foil/etched. The set filter still works: set only → browse the set; set + name → name search inside that set.
- **Bulk add** rows: "Rarity" chips (Common, Uncommon, Rare, Mythic, Special; `special` and `bonus` share the Special chip) select a card's base copy (nonfoil if it has one, else foil, else etched); "Foil" chips (opt-in) add an extra foil copy of cards that have both nonfoil and foil. Collector-number filter as now (numbers with suffixes such as `123a` or `★` match by their leading digits).
- **Find bar** also searches the type line (`typeLine`, saved from Scryfall `type_line`).
- **Share link** v2 payload: `{ v:2, n, r, c, p, s:[0 | [scryfallId, finishCode('n'|'f'|'e'), owned 0|1]] }`; the viewer fills names and pictures through `/cards/collection`.
- **Accent colour** violet `#8b5cf6` (hover `#7c3aed`) in place of MegaBinder's red. **Emblem**: an original faceted gem (a hexagonal crystal, violet facets, white highlight) inside a dark ring, drawn as inline SVG at 26×26 and by `tools/build_icons.py`, kept in the central 80 %. Not a mana symbol. Shown to Rob before he approves.

## Review Focus

1. A card name with quotes or punctuation (`"Ach! Hans, Run!"`, `Lim-Dûl's Vault`, `Fire // Ice`) still finds its printings: the exact-name query must escape `"` and the split name must match.
2. A set listing longer than one page (a 300+ card set, or Secret Lair with ~1500 cards) loads every page of `/cards/search`, in collector-number order, without passing ~10 requests/s.
3. A binder of 300+ cards prices in a handful of `/cards/collection` batches, and cards Scryfall no longer returns (`not_found`) are counted as "no price", not an error.
4. A saved or shared card whose picture is missing (Scryfall sometimes has no image yet) shows the name placeholder, and a double-faced card in a share link still flips.
5. Opening ManaBinder and MegaBinder on the same origin leaves the other's `pk…` keys and `megabinder-…` caches untouched.

---

### Task 1: MegaBinder cache fix (order of work step 1)

**Files:**
- Modify: `D:\code\megabinder\sw.js` (activate handler)
- Modify: `D:\code\megabinder\index.html` (`APP_VERSION`)

- [x] **Step 1:** In `activate`, delete a cache only when `k.startsWith('megabinder-') && ![CACHE_APP, CACHE_IMG].includes(k)`.
- [x] **Step 2:** Bump `APP_VERSION` `2026.11.14.1` → `2026.11.14.2`.
- [ ] **Step 3:** `git -C D:/code/megabinder diff` shows only those two lines. Leave uncommitted until Rob says "push it".

### Task 2: Copy, git init, strip Pokémon parts, rename keys

**Files:**
- Create (copied from MegaBinder): `index.html`, `sw.js`, `manifest.webmanifest`, `tools/build_icons.py`, `.gitignore`
- Not copied: `jp-gap.json`, `jp-en.json`, `zh-en.json`, `tools/build_jp_gap.py`, `tools/build_zh_en.py`, `README.md`, the PNG icons (rebuilt in Task 5)

**Interfaces:**
- Produces: constants `SK='mnBinder1'`, `SK_SETS='mnSets1'`, `SK_SYNC='mnSync1'`, `SK_FIT='mnFit1'`, `SK_FX='mnFx1'`, `GIST_DESC`, `GIST_FILE`, `APP_VERSION='2026.11.14.1'`; `FL = { nonfoil:'Normal', foil:'Foil', etched:'Etched' }`.

- [ ] **Step 1:** Copy the files, `git init`, `git config core.autocrlf false`, add `.gitattributes` with `* text=auto eol=lf` and `*.png binary`.
- [ ] **Step 2:** Remove from `index.html`: language selects (`add-lang`, `bulk-lang`) and their CSS, `LANG_*`, `langSets`/`loadLangSets`/`setsFor`, `jpGap`/`jpEn`/`zhEn` loaders and every `gap*` / `enOf` / `enSet*` / `withEn` use, `ART_EN*`, `IMG_TCGDEX`, `IMG_FALLBACK`, `fbImages`, `isStandIn`, `borrowedEn`, `ribbon` and `.artrib`/`.lbadge` CSS, `RARITIES` Pokémon lists, `autoFinish` and the `*_RARITY` lists, `upgradeArt` and its `pkArtChk1` key, the `@keyframes sh` holo/full-art/rainbow/gold CSS.
- [ ] **Step 3:** Rename keys, gist names, title, header text, manifest name/description (`A digital Magic: The Gathering binder: plan, track and price your collection.`), `sync` token link description (`manabinder`), accent colour tokens (`--acc`, see Decisions).
- [ ] **Step 4:** Verify: `grep -n "pk[A-Z]\|tcgdex\|pokemon\|Pok" index.html sw.js manifest.webmanifest` prints nothing (except the comment in `sw.js` that names MegaBinder's prefix, if any).

### Task 3: Scryfall data layer

**Files:**
- Modify: `index.html` (the former "TCGdex API" section)

**Interfaces:**
- Produces:
  - `sf(path: string, opts?: RequestInit) => Promise<object>`: queued fetch of `https://api.scryfall.com${path}`, ≥100 ms between starts, retries 429/5xx with backoff, throws `Error(details)` on Scryfall error objects except a 404 search, which returns `{ data: [] }`.
  - `sfAll(path) => Promise<object[]>`: follows `next_page` until `has_more` is false.
  - `toCard(j: ScryfallCard) => Card`: the add-dialog shape `{ id, name, number, rarity, finishes, layout, typeLine, set:{id,name}, images:{ thumb, small, large, back?, backLarge? } }`.
  - `loadSets()` fills `allSets: {id, name, released}[]` newest first (cached a week in `mnSets1`, filtered per Global Constraints).
  - `searchPrints(name: string, setId?: string) => Promise<Card[]>`: exact name `!"…"` (quotes escaped) plus `game:paper`, `unique=prints`, `order=released`, `dir=desc`, `include_extras=true`, `include_variations=true`; with a set, a contains-name search inside `e:<set>` instead.
  - `fetchSetCards(setId) => Promise<Card[]>`: whole set in collector-number order (`order=set`), cached in memory for the session (12 sets max).
  - `cardDetail(scryfallId) => Promise<ScryfallCard>` (memoised in `cardDetailCache`), `fetchDetails(ids, alive, onTick)` now batches `/cards/collection` in 75s and also fills `cardDetailCache`.
  - `priceOf(j, finish, fx) => { v, est, link, updated }`.

- [ ] **Step 1:** Implement the functions above. Header `Accept: application/json` on every call.
- [ ] **Step 2:** Browser check (console on `http://localhost:8765/`): `await searchPrints('Lightning Bolt')` returns > 30 cards, first has the newest `released`; `await searchPrints('Fire // Ice')` and `await searchPrints('Lim-Dûl\'s Vault')` return ≥ 1; `(await fetchSetCards('sld')).length > 175`; `allSets.some(s => s.id === 'tdsk' )` is `false` (tokens excluded) and `allSets.some(s => s.id === 'sld')` is `true`.
- [ ] **Step 3:** Network panel shows no two Scryfall requests starting < 100 ms apart during `fetchSetCards('sld')`.

### Task 4: UI wired to Scryfall (add, bulk, popup, value, shopping list, share)

**Files:**
- Modify: `index.html`

**Interfaces:**
- Consumes: everything Task 3 produces.
- Produces: `entryFrom(card: Card, finish: string, owned?: boolean) => SlotRecord` used by `doAdd` and `doBulkAdd`; `flipDet()` for the popup's flip button.

- [ ] **Step 1: Add dialog.** Name autocomplete dropdown (`#name-drop`, reuse `.acdrop`), printings grid (tile label: set name, `#number`, set code), finish buttons in `#sel-area`, set filter browse.
- [ ] **Step 2: Bulk add.** Rarity and Foil chip rows per Decisions; `doBulkAdd` uses `entryFrom`.
- [ ] **Step 3: Popup.** Flip button (`↻ Flip`, shown only when `imageBack`) swaps front/back pictures; price line `usd(v)` with "Buy on TCGplayer ↗" (`purchase_uris.tcgplayer`) or the ≈ EUR line; meta line `set · #number · Rarity`, finish line `✦ Foil` / `✦ Etched`.
- [ ] **Step 4: Value and shopping list** use `fetchDetails` (collection batches) and `priceOf`; remove the "several minutes" big-lookup warning threshold down to a plain progress bar (batches make it fast); shopping list search fallback `https://www.tcgplayer.com/search/magic/product?q=…`.
- [ ] **Step 5: Share link v2** (`packBinder` / `unpackBinder` per Decisions); `initShared` renders placeholders then fills them from `fetchDetails`.
- [ ] **Step 6: Finish looks.** `.f-foil` = static stripes + light frame (MegaBinder's reverse-holo style, no animation), `.f-etched` = a static warm/silver double frame; badges `.fb-foil` "Foil", `.fb-etched` "Etched"; `.land` contain style.
- [ ] **Step 7: Browser check.** Make a 3×3 binder; add Lightning Bolt picking a specific printing and Foil; add Delver of Secrets (transform) and flip it in the popup; bulk add a small set (e.g. `ltr` filtered to numbers 1-20) with two cards marked Need; Binder value shows totals and Most valuable; Shopping list shows the two needed cards with Buy links; Share link opens in a new tab read-only with the same pictures; find bar `creature` matches by type line; quick menu (right-click) mark/undo remove works.

### Task 5: Emblem, icons, manifest, service worker, CLAUDE.md

**Files:**
- Modify: `index.html` (two inline SVGs: header `.logo` and `.r-logo`), `tools/build_icons.py`, `sw.js`, `manifest.webmanifest`
- Create: `icon-192.png`, `icon-512.png`, `apple-touch-icon.png` (generated), `CLAUDE.md`

- [ ] **Step 1:** Emblem SVG per Decisions in both places; `build_icons.py` draws the same shapes (gem inside ring, ≤ 64 % of the icon width); run `python tools/build_icons.py`.
- [ ] **Step 2:** `sw.js`: caches per Global Constraints, `IMG_HOST = 'cards.scryfall.io'`, `SHELL` without the JSON data files, activate prefix rule.
- [ ] **Step 3:** `CLAUDE.md` carrying over: one file, `APP_VERSION` bumps, don't rename keys/gist names, PWA + network-first worker + `SHELL`, icons and the 80 % rule, subtle effects / only the page slide, no manual finish picker, navigation/fit notes, drag-and-drop deferred, LF + `autocrlf false`, Rob reviews before every push, never handle tokens; plus the Scryfall rules, the same-origin rules (`mn` keys, `manabinder-` caches, scope, gist names) and the card-record notes above.
- [ ] **Step 4:** Verify: the app's Application panel lists only `manabinder-app-v1` / `manabinder-img-v1` from this worker, manifest loads with both icons.

### Task 6: Final check, cleanup, hand to Rob

- [ ] **Step 1:** At 1280×800 (sidebar), 375×812 (top rail), 904×2316-ish Fold-open and 904/2 folded widths, and in fit mode: `document.documentElement.scrollWidth <= innerWidth` is `true`; the emblem shows in the rail.
- [ ] **Step 2:** Sync stays off with no token; the ☁ dialog shows `ManaBinder version 2026.11.14.1`.
- [ ] **Step 3:** Unregister the service worker and delete the caches this check created (`manabinder-*`; nothing else exists on `localhost:8765` from MegaBinder unless it was opened there — leave anything not ours alone), and remove the test binder keys from `localhost` storage.
- [ ] **Step 4:** Show Rob the emblem (rendered icon PNG). Stop for Rob's review; nothing is committed.
