---
name: analytics
description: Read the creator's own TikTok, Instagram, Facebook and YouTube analytics in his Chrome (Claude in Chrome) and explain in plain words where viewers drop off, what's working and what to change. Use when he asks how his videos are doing, why one flopped or blew up, where people swipe away, for a weekly check-in, or to compare platforms.
---

# Reading his analytics

No Meta developer account or API is needed: everything here is on pages he can already open while logged in.
Use the Claude in Chrome tools (load them with ToolSearch: `select:mcp__claude-in-chrome__tabs_context_mcp,
mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,
mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__tabs_create_mcp`). If Chrome isn't connected, tell him to
open Chrome and check the Claude extension is signed in.

**Look only.** Never post, delete, edit, reply, like, follow, boost or promote, change a setting, or accept a
prompt or terms. If a page asks him to log in, ask him to do it himself, then carry on.

## Where to look
Page layouts change often: if something isn't where it's described, find it through the page's own menus,
and say what you couldn't find instead of guessing.
- **TikTok**: tiktok.com/tiktokstudio -> Analytics (overview), and Posts -> a video -> its analytics:
  retention graph, average watch time, watched full video %, traffic sources (For You, Search, Profile), new viewers.
- **Instagram and Facebook**: business.facebook.com/latest/insights -> Content (or a reel's "View insights" on
  instagram.com): views, average watch time, skip rate (swiped away in the first 3 s), the retention graph,
  shares, saves, follows.
- **YouTube Shorts**: studio.youtube.com -> Analytics -> Content -> Shorts, then each Short: "viewed vs swiped away",
  average view duration, average percentage viewed, the audience retention graph.

## What to collect
The last 10-20 videos (or the ones he names), one row per video and platform: date, length, views,
average watch time, % watched / average % viewed, swiped away / skip rate, shares, saves, follows if shown.
For the videos that matter most (best, worst, newest), read the retention graph (zoom in on the screenshot):
- steep drop in the first 1-3 s -> the hook (first shot, first line, on-screen text)
- a steady slide -> pacing (pauses, shots held too long, nothing new every few seconds)
- a sudden drop at one moment -> something there (a slow line, a confusing cut, an early payoff)
- a bump -> a moment people rewatch: do more of that

If the video was made in this project (`out/<name>/` exists), open `public/<name>/edit.json` and `words.json` and
say exactly what was on screen and being said at the drop: "38% leave at 0:03, right as the hook text disappears
and the second clip starts."

## Report
Write `reports/analytics-YYYY-MM-DD.md`, short and in plain words:
1. Top 3 and bottom 3 videos and what separates them
2. Where people leave (hook, middle, end) with the exact moments
3. Platform differences worth knowing
4. 3-5 concrete changes for the next videos (hook style, length, pacing gap, captions, topics)

Then add anything new and solid (seen in several videos, not a one-off) to `reports/learnings.md`, a running list of
what works for him. The make-video and research skills read it before editing or writing scripts.
