---
name: research
description: Market research in the creator's niche plus script writing - find creators and videos that are performing well on TikTok, Instagram and YouTube Shorts, break down why (hook, format, length, pacing, topic), compare with his own videos, and write voiceover scripts and hook options for him to record. Use when he asks for video ideas, competitors, what's trending or working in his niche, who's doing well, or to write or improve a script.
---

# Research and scripts

Read `brand.json` (niche, handles) and `reports/learnings.md` first. Browse with the Claude in Chrome tools (see the
analytics skill for how to load them). Behave like a person browsing: public pages only, no bulk downloading or
scraping. Never follow, like, comment or message anyone. Never copy someone's script: borrow the structure and
write his own words.

## Find what's working
- Search his niche keywords on TikTok (tiktok.com/search?q=..., Videos tab), Instagram (hashtag and Reels pages)
  and YouTube (youtube.com/results?search_query=...+shorts, filter by this month or this year).
- Look for **outliers**: videos with far more views than that creator usually gets (5-10x their normal views, or
  more views than they have followers). That means the idea worked, not just the account size.
- 10-20 outliers per round. For each: creator, followers, views, date, length, link.

## Break each one down
- **Hook**: the first spoken line and the on-screen text in the first 2 s (screenshot the opening frame)
- **Format**: talking to camera, voiceover over clips, list, story, tutorial, before/after, reaction
- **Length and pace**: seconds, roughly how often it cuts, how fast it gets to the point
- **Topic angle** and **ending** (payoff, loop back to the start, call to action)
- Captions/description: `get_page_text`

Then list the patterns that repeat across the outliers, and how his recent videos compare (his own analytics
report if there is one).

Save `research/YYYY-MM-DD-<topic>.md`: the table, the patterns, "what this means for you", and 5-10 video ideas
that fit footage he can realistically film.

## Scripts
When he wants scripts, write 20-60 s voiceovers that sound like him (his past transcripts are in the `speech`
fields of `library/index.json`):
- **Hook**: the first sentence, under ~2 s / 6-10 words: a promise, a surprise or tension. Give 3 options.
- **Body**: one idea per sentence, short sentences, something new every 3-5 s, no intro, no "hey guys".
- **Payoff** before the end; the last line loops back to the first or gives a clear reason to follow.
- Mark where B-roll should show what's being said, the on-screen hook text, and 2-4 moments (zoom, text, emoji).

Save to `research/scripts/<name>.md`. He records it, drops the recording in his footage folder and says
"make the video from <name>".
