# ManaBinder

A digital binder for a physical Magic: The Gathering collection. Lay out your cards as binder pages, find the exact printing you own, plan the cards you still need, and see what the collection is worth.

**Open the app: https://rstibal.github.io/manabinder/**

It runs in the browser on a phone, tablet or computer, and can be installed to the home screen like an app. There's nothing to sign up for.

## What it does

- **Binders and pages.** Make as many binders as you like, each with its own page size (rows × columns). Turn pages with the buttons or by swiping.
- **The exact printing.** Type a card name, then pick the printing by set, collector number and art, newest first. Or pick a set and add cards from it in bulk, filtered by rarity.
- **Finishes.** Normal, Foil and Etched come from the printing itself; a card printed in more than one finish offers each as its own choice.
- **Double-faced cards.** The slot shows the front; the card popup has a flip button for the back.
- **Planning.** Mark a card as "need" and it shows greyed out in its slot, so a binder can be laid out before it's complete. The shopping list collects every needed card with its price.
- **Prices.** TCGplayer prices in US dollars by finish, with a link to buy. Where there's no US price, a Cardmarket euro price is converted and marked ≈. Prices update about once a day.
- **Find, filter and rearrange.** Search a binder, filter what's shown, move cards around with the layout unlocked, and undo from the quick menu (right-click or long-press).
- **Fit to screen.** Sizes the cards so a whole page fits the window.
- **Share links.** Send a read-only link to a binder; the viewer doesn't need anything installed.

## Where your data lives

Your binders are saved in your browser on your device. Nothing leaves the device unless you turn on cloud sync, which is optional: it copies your binders to a private GitHub gist so other devices can use them. It needs a GitHub account and a classic token with only the `gist` scope.

Clearing your browser's site data deletes your binders, so turn on sync if you want a copy kept somewhere else.

## Card data

Card information, pictures and prices come from [Scryfall](https://scryfall.com). English cards only. Exchange rates come from [frankfurter.dev](https://frankfurter.dev).

ManaBinder is free and always will be. It isn't affiliated with or endorsed by Wizards of the Coast or Scryfall. Magic: The Gathering and its card images are © Wizards of the Coast.

## Feedback

This is version one, being tested by a Magic collector. If something is missing or wrong, [open an issue](https://github.com/rstibal/manabinder/issues).

## For developers

One `index.html` (plain HTML, CSS and JavaScript, no build step or dependencies), plus a service worker (`sw.js`), a web manifest and icons. To run it locally:

```bash
python -m http.server 8766
```

Then open http://localhost:8766/. `CLAUDE.md` has the working rules and `docs/superpowers/specs/` the design.
