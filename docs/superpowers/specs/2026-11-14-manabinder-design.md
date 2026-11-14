# ManaBinder: design

Date: 2026-11-14. Status: draft for review.

## Intent

ManaBinder is MegaBinder for Magic: The Gathering cards. Rob is building it for a friend who collects Magic. Neither Rob nor Claude knows how the friend collects (binders, boxes or decks), so version one deliberately copies MegaBinder's features and look with Magic card data in place of Pokémon. The friend tests the basics, and his feedback decides what version two adds or drops.

Success for version one: the friend can open a link on his phone or computer, make a binder, find his cards (the exact printing), see them laid out as binder pages with prices, and tell Rob what's missing.

## Goals

- Same binder experience as MegaBinder: binders of rows × columns pages, page turns (buttons, swipe, ~180 ms slide), the card popup, the planner (cards marked "need" shown greyed out), find and filter, the quick menu (right-click / long-press) with undo, rearranging behind the "Layout locked" toggle, binder value, shopping list, read-only share links, fit to screen, the icon-rail and sidebar layouts, installable as an app (PWA).
- Card data, images and prices from Scryfall (`https://api.scryfall.com`).
- Finding the exact printing: a Magic card can have dozens of printings, so adding a card means picking the card and then the printing (set, collector number, art).
- Finish is automatic from the printing: Normal, Foil or Etched, from Scryfall's `finishes` list. A printing offered in more than one finish is offered as separate choices when adding, as MegaBinder does for reverse holos.
- Double-faced cards: the binder slot shows the front face; the popup has a flip button for the back.
- Cloud sync stays, and stays optional: off until someone connects a GitHub token, cards saved only on the device until then. The friend may not have a GitHub account.

## Non-goals (version one)

- Languages other than English.
- Deck building, legality checks, playing the game.
- Prices in currencies other than USD (EUR may be used as an estimate where USD is missing, as MegaBinder does).
- Card scanning with the camera.
- Anything MegaBinder doesn't already do, unless the friend asks for it.

## Anti-goals

- Touching MegaBinder's data in any way (see "Living next to MegaBinder" below). Losing Rob's Pokémon collection would make this a failure even if ManaBinder works.
- Using Wizards of the Coast's logos, mana symbols or the Magic name as branding. ManaBinder gets its own emblem.
- Animated effects. The only motion is the quick page-turn slide (same rule as MegaBinder).
- A build step or libraries: one `index.html`, vanilla HTML/CSS/JS.

## Constraints

### Living next to MegaBinder (important)

Both apps will be served from the same origin, `rstibal.github.io` (`/megabinder/` and `/manabinder/`). Browsers share `localStorage` and the Cache Storage across one origin, so:

1. **Storage keys must all differ.** MegaBinder uses `pkBinder4`, `pkSets6`, `pkSync1`, `pkFit1`, `pkFx1` and others with a `pk` prefix. ManaBinder uses an `mn` prefix for every key (for example `mnBinder1`, `mnSync1`, `mnFit1`). No `pk` key may be read or written.
2. **Service worker caches.** MegaBinder's `sw.js` currently deletes *every* cache that isn't one of its own when it activates, which would wipe ManaBinder's caches (and a copied ManaBinder worker would wipe MegaBinder's). Fix both: each worker deletes only old caches with its own prefix (`megabinder-` / `manabinder-`). The MegaBinder change ships first, with its own `APP_VERSION` bump.
3. **Service worker scope.** Each worker is registered from its own folder, so its scope is `/megabinder/` or `/manabinder/`. Keep it that way.
4. **Sync gist names.** ManaBinder uses its own gist description and file name (`manabinder data (do not edit)`, `manabinder.json`), so it never finds or overwrites the Pokémon gist even if the same GitHub account is used for both.
5. **Share links** use the app's own URL, so they don't clash.

### Scryfall rules

- At most about 10 requests a second (50–100 ms apart). Bulk queries go through `/cards/search` (175 cards a page) rather than card-by-card lookups.
- Use Scryfall's image URLs directly; don't copy or re-host images.
- The app stays free (Scryfall requires that data not be paywalled).
- Browsers can't set a custom User-Agent; that's fine. Send `Accept: application/json`.
- Prices on Scryfall are updated about once a day and only as recent as that.

## How it gets made (Claude's calls, for Rob to check)

- **Start from a copy of MegaBinder's files** in `D:\code\manabinder`, then remove what is Pokémon-specific and swap TCGdex for Scryfall. It's not a shared code base: from then on the two apps are separate files and repos.
- **Removed:** Japanese and Chinese support (`jp-gap.json`, `jp-en.json`, `zh-en.json`, their build scripts, the language picker and badges, `ART_EN` stand-in art), the TCGdex image fallbacks (`IMG_TCGDEX`, `IMG_FALLBACK`), the Pokémon rarity lists and finish rules (Full Art / Gold / Rainbow / Rev. Holo), and the art-upgrade check.
- **Card record** saved in a slot: Scryfall id, name, set name, set code, collector number, rarity, finish, small and large image URLs, plus the back face's images for double-faced cards. Same shape and field roles as MegaBinder's, renamed where a field is Pokémon-specific (for example `scryfallId` instead of `tcgId`).
- **Sets:** from `/sets`, cached for a week. Left out: digital-only sets, tokens, art series, memorabilia and minigame sets. Everything else is kept, including promos and Secret Lair.
- **Adding a single card:** type a name (Scryfall autocomplete), pick from the list of printings (set, number, art thumbnail, newest first), then the finish if there's more than one. Picking a set first and browsing it also works, as in MegaBinder.
- **Bulk add by set:** pick a set, filter by rarity (Common, Uncommon, Rare, Mythic, plus Special/Bonus) and finish (normal copies, foil copies), mark cards as owned or needed, add them in collector-number order. Same flow as MegaBinder's bulk add.
- **Prices:** TCGplayer USD from Scryfall (`usd`, `usd_foil`, `usd_etched`, matching the finish). If there is no USD price, Cardmarket EUR converted to USD and marked ≈, as now. The buy link is the printing's TCGplayer link from Scryfall (`purchase_uris.tcgplayer`).
- **Finish look:** subtle and static. Foil reuses the reverse-holo style idea (light stripes and frame, no motion); Etched gets a slightly different static frame. Normal has no effect. Small badge text: "Foil", "Etched". MegaBinder's animated holo shimmer is not carried over.
- **Look and name:** MegaBinder's dark layout and card grid. The Poké Ball emblem is replaced by a ManaBinder emblem drawn the same way (an inline SVG in the header, and `tools/build_icons.py` for the home-screen icons, kept inside the central 80%). The emblem must be original, not a mana symbol. Accent colour may change from MegaBinder's.
- **Hosting:** a new public GitHub repo `rstibal/manabinder` with GitHub Pages from `main`, at `https://rstibal.github.io/manabinder/`. Creating the repo and turning on Pages are done only after Rob says so.
- **Project notes:** a `CLAUDE.md` for ManaBinder carrying over the rules that still apply (one file, `APP_VERSION` bumps, network-first service worker, subtle effects, no manual finish picker, LF line endings, Rob reviews before every push), plus the Scryfall and same-origin rules above.

### Settled after review (Claude's calls)

- **Double-faced cards** means Scryfall layouts whose faces each have their own picture (transform, modal double-faced, meld, reversible). Split, adventure and flip cards are one picture and need no flip button.
- **Landscape cards** (Battles, Planechase planes, split cards) show in the normal upright slot, shrunk to fit, not rotated.
- **Binder value and shopping list** fetch prices in batches of up to 75 cards through `/cards/collection`, not one request per card.
- **Offline pictures:** the service worker caches card images from `cards.scryfall.io` as you browse, bounded like MegaBinder's picture cache, so binders still show offline.
- **Share links** carry only what's needed to redraw the binder (Scryfall id, finish, need flag and slot layout); the viewer looks up names and pictures, so links stay short.

## Left to the builder

- Exact layout of the printing picker inside the existing add dialog.
- Exact list of excluded set types beyond those named, after looking at `/sets`.
- The emblem's design and the accent colour (show Rob before finalizing).
- How the flip button looks in the popup.
- Whether the find bar also searches card type text (a cheap addition, the builder's call).

## Order of work

1. MegaBinder: make `sw.js` delete only its own old caches; bump its version. (Pushed after Rob's OK.)
2. Copy MegaBinder into `D:\code\manabinder`, `git init`, strip the Pokémon parts, rename storage keys and gist names.
3. Scryfall: sets, name search with printings, set browsing, bulk add, card details and prices, double-faced cards.
4. Finish badges and looks; emblem and icons; manifest and service worker.
5. Check locally at desktop and phone widths (and fit mode), then Rob decides about the GitHub repo and Pages.
