# AnkiDocComments

Add Google Docs-style inline comments to your cards right inside the Anki Reviewer.

I built this because throwing notes into an `Extra` field gets messy fast on long cards—sometimes you just want to highlight a specific phrase and attach a note to it. Comments are saved directly inside the note's field HTML, so everything syncs over AnkiWeb and stays readable on mobile without any external database.

<!-- ![Demo](docs/demo.png) -->

## What it does
<img width="1127" height="599" alt="image" src="https://github.com/user-attachments/assets/4eb87725-b643-4e1c-b5e2-ee471ab6c0a7" />
<img width="968" height="506" alt="image" src="https://github.com/user-attachments/assets/ee075c19-f31e-42da-92f9-d2d7e15c1c40" />


**On Desktop (full editing):**
- Select text in the Reviewer (front or back), right-click, and pick **Add comment**.
- Format notes with bold, italics, underline, lists, blockquotes, links, text color, and click-to-reveal spoilers.
- Reply in threads, edit or delete individual replies, delete the whole thread, or mark it as resolved.
- Open comments on hover or click (configurable), with light and dark mode support.
- Uses your current Anki profile name as the author.
<img width="1351" height="726" alt="image" src="https://github.com/user-attachments/assets/81b3e2f9-5273-458c-a4c3-6a2d4aab87ee" />

**On Mobile — AnkiDroid / AnkiMobile (read-only):**
- Tap highlighted text to read threads, reveal spoilers, and follow dark mode styling.
- Runs via a snippet injected into your card template (no mobile add-on needed, and automatically skips on desktop).

## Installation

Download or clone this repo into your Anki `addons21` directory, then restart Anki:

- **Windows:** `%APPDATA%\Anki2\addons21\AnkiDocComments`
- **macOS:** `~/Library/Application Support/Anki2/addons21/AnkiDocComments`
- **Linux:** `~/.local/share/Anki2/addons21/AnkiDocComments`

Targets Anki 2.1.50+ (point versions 50–65 in `manifest.json`).

## Usage

### Desktop
Highlight text -> right-click -> **Add comment** -> save.

If the exact phrase you selected shows up in multiple fields on the same note, a dropdown will pop up asking which field to save it to. If you want the add-on to pick the right field automatically.


## Disclaimer

Because this add-on writes directly to your note fields, it's worth being clear about what happens to your data.

Your notes stay safe and portable. Everything is saved as standard HTML (`<mark>` and a hidden `<div>`) rather than a proprietary format, so uninstalling the add-on won't break your cards or lock you in. Every edit also creates an Anki undo checkpoint (`Ctrl+Z` / `Cmd+Z`), and if you injected the mobile script into a note type, you can strip it cleanly anytime via **Tools → AnkiDocComments → Remove mobile script from a note type...**.

There are no external servers, tracking, or background syncs—everything stays inside your Anki collection and your own AnkiWeb account. Just keep in mind that your current Anki profile name is saved as the author on each comment, so anyone you export an `.apkg` to will see that name.

As with any add-on that modifies note data, keeping regular Anki backups is always a good idea—especially if your templates run custom JavaScript that rewrites the card DOM. This is an open-source project provided as-is under the MIT license, and future Anki updates may occasionally require adjustments.

