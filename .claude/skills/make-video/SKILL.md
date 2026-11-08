---
name: make-video
description: Edit a short vertical video (TikTok, Instagram Reels, Facebook Reels, YouTube Shorts) from the creator's own footage - a voiceover laid over clips, or a talking-to-camera recording cut into jump cuts - with tight pacing, captions, B-roll, small animations, a live preview and a checked final render. Use whenever he asks to make, edit, cut down, caption, re-cut, preview, change or render a video, or says "make one from <file>".
---

# Making a video

He supplies everything (voiceovers, clips, raw recordings). Claude never generates voices or video, never posts,
and never moves, renames, edits or deletes anything in his footage folders.

Each video has a short name (lowercase-with-dashes, e.g. `gym-tips-3`); its working files live in `public/<name>/`.
Before starting, read `reports/learnings.md` if it exists: what has worked for him so far.

## 1. Catalog
`py -3.12 tools/index.py` (quick when nothing is new). `library/index.json` has, per file: `kind` (video/audio),
`dur`, `shape` (upright/sideways), `speech` (timestamped lines, empty if nobody talks), `sheet` (a grid of stills:
open it with Read to see what's in the clip) and `sheet_times` (the second each still was taken).
If he names a file loosely ("the gym one"), match it against names, folders and speech. Ask only if it's still unclear.

## 2. Pacing
`py -3.12 tools/pace.py "<file>" <name>`
- An audio file is a **voiceover**: produces `voice.wav` (pauses cut to ~0.15 s, ums and repeated takes removed, never sped up).
- A video file is **talking to camera**: produces jump cuts of the recording, with a slight punch-in on every other cut.
- Long recording, short video: find the strongest 20-60 s in its `speech` lines (a complete thought with a hook
  at the start and a payoff at the end), then add `--from <s> --to <s>`.
- Read `public/<name>/transcript.txt`: cut words are in [brackets]. If a real word was cut, rerun with
  `--keep-retakes` or `--keep-fillers`. "More breathing room" = `--gap 0.25`, "tighter" = `--gap 0.1`.
- It writes a starter `edit.json` the first time. Rerunning it later changes the timing, so redo the clip timings after.

## 3. Footage (voiceover videos)
Fill `clips` in `public/<name>/edit.json`: the pictures, back to back, covering the whole voice.
- Split the voiceover into beats with `words.json` (word start/end seconds). Cut on phrase boundaries.
- Per beat, pick the clip that shows what's being said: open the sheets, choose `in` with `sheet_times`.
- The first 1-2 s get the most eye-catching shot. Clips 1.5-3 s each, quicker (~1 s) in lists or high energy,
  longer on the payoff. Never the same clip twice in a row; avoid reusing one in a video.
- Sideways footage: set `focus` (0 = keep the left side, 0.5 middle, 1 right) so the subject stays in the upright frame.
- Nothing fits: `py -3.12 tools/stock.py "plain visual description" 3` (free Pexels clips), look at the new sheets, pick one.
  His own footage always comes first.

## 4. Talking to camera
The jump cuts are already in `clips` (with sound). Add 2-5 `broll` overlays where he describes something you can
show (`at` = that word's start in words.json, `dur` 1.5-3 s). Keep his face visible during the first 3 s and the punchline.

## 5. Extras
- `hook`: 3-7 words on screen for the first ~2 s. It adds to the first spoken line instead of repeating it.
- `moments`: 2-4 per video, at key beats only, never two at once:
  `zoom` on an emphasis word, `text` for a key number or claim (5 words max), `emoji` for a reaction.
- `captions`: always on (most people start watching muted). `progress`: on for videos over ~30 s.
- `music`: off unless he asks (trending sounds added inside the app usually reach more people).

## 6. Preview and changes
`py -3.12 tools/prep.py <name>` checks the edit (plain-language errors) and builds it. Then open the preview:
start the `studio` server from `.claude/launch.json` (or `npm run studio` -> http://localhost:3000) and pick
`<name>` in the left sidebar. Tell him in 2-3 lines what you did (length, number of cuts, the moments) and ask
what to change. After each change: edit `edit.json`, run prep again, and the preview reloads by itself.

| He says | Change |
|---|---|
| bigger / smaller captions | `"style": {"size": 90}` (default 76) |
| captions higher / lower | `"style": {"y": 0.5}` (0 = top, 1 = bottom; stay between 0.3 and 0.7, clear of the app buttons) |
| other caption colour / font | `"style": {"highlight": "#hex", "font": "Anton"}` (Montserrat, Poppins, Inter, Anton, BebasNeue); for every video: brand.json |
| cut that shot earlier / later | shorten that clip's `dur`, lengthen the next (total must still cover the voice) |
| swap a shot | new `src` / `in` |
| no zoom on cuts | every clip `"zoom": 1` |
| more / less animation | add / remove `moments` |

## 7. Render
`py -3.12 tools/render.py <name>` -> `out/<name>/<name>.mp4` (1080x1920, works on all four apps), `checks.txt`, `sheet.jpg`.
Fix every `PROBLEM` line; look at `sheet.jpg` once. Then write `out/<name>/post.txt`, one block each:
- **TikTok**: caption under 150 characters, 3-5 hashtags
- **Instagram Reels**: hook as the first line, 1-2 short lines, 3-5 hashtags
- **YouTube Shorts**: title under 60 characters (curiosity + the main keyword), 2-3 hashtags
- **Facebook Reels**: 1-2 sentences, 1-3 hashtags

He posts it himself.

## edit.json reference
```json
{
  "voice": "voice.wav",
  "clips":  [{"src": "C:/.../clip.mp4", "in": 2.0, "dur": 2.5, "focus": 0.5, "zoom": 1, "audio": false}],
  "broll":  [{"src": "C:/.../other.mp4", "in": 0, "dur": 2, "at": 6.2, "focus": 0.5}],
  "hook": {"text": "He lost $20 to a prank", "dur": 2},
  "moments": [{"kind": "zoom", "at": 5.6, "dur": 1.2, "amount": 0.12},
              {"kind": "text", "at": 8.6, "dur": 1.6, "text": "$784,000", "y": 0.32},
              {"kind": "emoji", "at": 10.2, "dur": 1.4, "emoji": "😳", "x": 0.72, "y": 0.42}],
  "captions": true, "progress": false,
  "music": {"src": "C:/.../track.mp3", "volume": 0.12},
  "style": {"size": 76}
}
```
`voice` is null for talking-to-camera (the sound comes from clips with `"audio": true`). All times in seconds;
`at` is seconds into the finished video, `in` is seconds into the source file.
