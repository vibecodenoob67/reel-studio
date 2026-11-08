# Reel Studio

Claude edits extra short videos from your own footage so you can post more, more consistently:

- **Edits**: cuts your voiceover or talking clip to a tight pace (no dead air, ums or retakes, never sped up),
  matches your clips to what you're saying, adds B-roll, captions, a hook and a few small animations,
  and renders one upright video for TikTok, Reels, Facebook and Shorts.
- **Analytics**: reads your TikTok, Instagram, Facebook and YouTube stats in your Chrome and tells you where people
  swipe away and what to change. No developer accounts or APIs needed.
- **Research**: finds videos doing unusually well in your niche, breaks down why, and writes scripts for you to record.

You watch every video in a preview and say what to change before anything is final. Claude never posts for you
and never changes your original files.

## Install (once, about 15 minutes)
1. Make a free GitHub account (github.com) and accept the invite to the **reel-studio** repository
   (it arrives by email and on github.com/notifications).
2. Install the Claude desktop app (claude.ai/download), sign in, open the **Code** tab.
3. For analytics and research: install **Claude in Chrome** from the Chrome Web Store and sign in with the same account.
4. In the Code tab, say:
   *"Install Git if it's missing, then clone https://github.com/vibecodenoob67/reel-studio into
   C:\Users\<your name>\reel-studio and run setup.ps1"*
   The first time, a GitHub sign-in window pops up: sign in with the account that accepted the invite.
   (Keep it in a short folder like that one; very long folder paths break rendering on Windows.)
5. Open that folder in the Code tab and say **"set me up"**. Claude asks where your footage is and a few questions.

Tip: if your footage is on OneDrive, right-click the folder -> **Always keep on this device**.

## Things you can say
- "Make a video from the gym-tips voiceover"
- "Cut monday-talk.mp4 down to a 40 second video"
- "Find the best 3 short videos in podcast-ep4.mp4"
- "Bigger captions, and swap the second shot for something outdoors"
- "Render it"
- "How did my last 10 videos do? Where are people dropping off?"
- "Who's doing well in my niche right now? Write me 3 scripts."
- "Update the project" (gets the newest version)

## Good to know
- Finished videos land in `out/<video name>/` with a ready-to-paste caption for each app (`post.txt`).
- Free stock clips (Pexels) are optional: Claude explains the free key if you want it.
- The editor is built on Remotion, which is free for individuals and companies of up to 3 people.
