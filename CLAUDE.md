# Reel Studio

Claude edits short vertical videos (TikTok, Instagram Reels, Facebook Reels, YouTube Shorts) from the creator's own
footage, reads his analytics in his Chrome, and researches his niche. He reviews everything. Claude never posts.

## Skills: load the one that fits
- **make-video**: making, changing, previewing or rendering a video
- **analytics**: how his videos are doing, where viewers drop off
- **research**: what works in his niche, video ideas, scripts

## First run (no brand.json yet)
1. Ask him, a question or two at a time: his name or brand, his niche and who it's for, his handles, the folder
   his footage lives in (often OneDrive, e.g. `C:/Users/<him>/OneDrive/Content`), optionally a folder for finished
   videos, and whether he wants a caption look other than the default (white words, yellow active word, Montserrat).
2. Copy `brand.example.json` to `brand.json` and fill it in (forward slashes in paths).
3. If the folder is on OneDrive, tell him to right-click it -> "Always keep on this device", so the videos are on the PC.
4. Run `py -3.12 tools/index.py` and tell him what's in his folder in a few lines.
5. Free stock B-roll is optional: a free key from pexels.com/api goes in `.env` as `PEXELS_API_KEY=...`.

## Tools (run from this folder)
| Command | Does |
|---|---|
| `py -3.12 tools/index.py` | catalog his footage (new files only) -> library/index.json |
| `py -3.12 tools/pace.py <file> <name>` | tighten a voiceover, or jump-cut a talking recording |
| `py -3.12 tools/stock.py "<words>" 3` | free upright stock clips from Pexels |
| `py -3.12 tools/prep.py <name>` | check and build an edit for the preview |
| `npm run studio` | the preview (http://localhost:3000) |
| `py -3.12 tools/render.py <name>` | final mp4 + automatic checks -> out/<name>/ |
| `py -3.12 tools/test_pace.py` | self-check of the cutting rules |

## Rules
- His footage folders are read-only: never move, rename, change or delete anything in them.
- Never post, publish, delete, message, or change settings on his accounts.
- Talk to him in plain words, not code. Show him the preview before the final render.

## Updating
When he says "update the project": `git pull`, then `npm install` if package.json changed.
