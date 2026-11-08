"""Tighten the pacing of a voiceover or a talking-to-camera recording. Nothing is sped up.

    py -3.12 tools/pace.py <voiceover or raw video> <video-name> [--gap 0.15] [--min-pause S] [--keep-fillers] [--keep-retakes]

- pauses longer than --min-pause are cut down to --gap seconds (default from brand.json), cut inside the silence
- "um / uh / erm" are cut out
- false starts and repeated takes are cut, the LAST take is kept ("So the best - so the best way to...")
- audio file  -> public/<name>/voice.wav (the tightened voiceover)
- video file  -> jump cuts of the recording itself (the cut list goes into edit.json as clips with sound)
Also writes words.json (captions, already shifted to the new timing), transcript.txt (what was cut, in [brackets])
and a starter edit.json if the video doesn't have one yet.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np

from common import brand, probe, run, transcribe, video_dir

SR, HOP = 16000, 160  # 10 ms analysis frames
FILLERS = {'um', 'umm', 'uh', 'uhh', 'uhm', 'erm', 'er', 'ehm', 'ah', 'hmm', 'mm', 'mhm'}


def norm(w):
    return re.sub(r"[^a-z0-9']", '', w.lower())


def load(path, sr):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-vn', '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def retakes(words):
    """Indexes of words to drop: false starts / repeated takes. The later take always wins."""
    drop = set()
    toks = [norm(w['w']) for w in words]
    # 1. a run of 3+ words said twice in a row: "the best way to the best way to do it" -> drop the first run
    for n in range(8, 2, -1):
        for i in range(len(toks) - 2 * n + 1):
            if toks[i:i + n] == toks[i + n:i + 2 * n] and not drop & set(range(i, i + 2 * n)):
                drop.update(range(i, i + n))
    # 2. a phrase that restarts the next one ("Walt doesn't know that. Walt doesn't know that.")
    phrases, cur = [], []
    for i, w in enumerate(words):
        if cur and w['s'] - words[i - 1]['e'] > 0.6:
            phrases.append(cur)
            cur = []
        cur.append(i)
        if w['w'][-1:] in '.!?':
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    for a, b in zip(phrases, phrases[1:]):
        ta = [toks[i] for i in a if toks[i] not in FILLERS and i not in drop]
        tb = [toks[i] for i in b if toks[i] not in FILLERS and i not in drop]
        k = min(3, len(ta), len(tb))
        if k >= 2 and ta[:k] == tb[:k]:
            drop.update(a)
    return drop


def keep_ranges(x, words, drop, gap, min_pause):
    """Seconds of the source to keep, as [(start, end), ...]."""
    n = len(x) // HOP
    db = 20 * np.log10(np.sqrt((x[:n * HOP].reshape(n, HOP) ** 2).mean(1)) + 1e-9)
    floor, peak = np.percentile(db, 10), np.percentile(db, 99)
    speech = db > max(floor + 12, peak - 38)
    # clicks / blips under 50 ms inside silence are not speech
    edges = np.flatnonzero(np.diff(np.r_[0, speech.astype(np.int8), 0]))
    for a, b in zip(edges[::2], edges[1::2]):
        if b - a < 5:
            speech[a:b] = False
    # dropped words become silence, widened to the quiet around them but never into a kept word
    kept = [w for i, w in enumerate(words) if i not in drop]
    for i in sorted(drop):
        w = words[i]
        lo = max([k['e'] for k in kept if k['e'] <= w['s']], default=0)
        hi = min([k['s'] for k in kept if k['s'] >= w['e']], default=n / 100)
        a, b = int(w['s'] * 100), int(w['e'] * 100)
        while a > int(lo * 100) and speech[a - 1]:
            a -= 1
        while b < min(n, int(hi * 100)) and speech[b]:
            b += 1
        speech[a:b] = False
    # sound that touches no kept word (the tail of a cut take, a breath, a cough) counts as silence too
    spans = [(int(w['s'] * 100) - 5, int(w['e'] * 100) + 5) for w in kept]
    edges = np.flatnonzero(np.diff(np.r_[0, speech.astype(np.int8), 0]))
    for a, b in zip(edges[::2], edges[1::2]):
        if not any(s < b and e > a for s, e in spans):
            speech[a:b] = False
    keep = np.ones(n, bool)
    g2 = int(gap * 100 / 2)
    edges = np.flatnonzero(np.diff(np.r_[1, speech.astype(np.int8), 1]))
    for a, b in zip(edges[::2], edges[1::2]):  # silent runs [a, b)
        if a == 0:
            keep[:max(0, b - g2)] = False
        elif b == n:
            keep[a + g2:] = False
        elif (b - a) / 100 > min_pause:
            keep[a + g2:b - g2] = False
    edges = np.flatnonzero(np.diff(np.r_[0, keep.astype(np.int8), 0]))
    return [(a / 100, b / 100) for a, b in zip(edges[::2], edges[1::2])]


def remap(words, drop, ranges):
    """Word timings on the new, tightened timeline. Whisper's word edges are loose (a word may "start" in the pause
    before it), so a word stays if any of it survives, placed in the kept range it overlaps most."""
    out, starts, t = [], [], 0
    for a, b in ranges:
        starts.append(t)
        t += b - a
    for i, w in enumerate(words):
        lap = [min(w['e'], b) - max(w['s'], a) for a, b in ranges]
        k = int(np.argmax(lap)) if lap else 0
        if i in drop or not lap or lap[k] <= 0:
            continue
        a, b = ranges[k]
        out.append({'w': w['w'], 's': round(starts[k] + max(w['s'], a) - a, 3), 'e': round(starts[k] + min(w['e'], b) - a, 3)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('slug')
    ap.add_argument('--gap', type=float)
    ap.add_argument('--min-pause', type=float)
    ap.add_argument('--keep-fillers', action='store_true')
    ap.add_argument('--keep-retakes', action='store_true')
    ap.add_argument('--from', dest='start', type=float, default=0, help='use only this part of a long recording (seconds)')
    ap.add_argument('--to', dest='end', type=float)
    o = ap.parse_args()
    src = Path(o.src).resolve()
    d = video_dir(o.slug)
    info = probe(src)
    is_video = 'w' in info
    audio = src
    if o.start or o.end:  # a section of a long recording: work on that piece, keep times relative to the original
        audio = d / 'section.wav'
        r = run(['ffmpeg', '-v', 'error', '-y', '-ss', o.start, *(['-to', o.end] if o.end else []), '-i', src, '-vn', '-ac', '1', '-ar', 48000, audio])
        if r.returncode:
            raise SystemExit(r.stderr[:300])
        info['dur'] = probe(audio)['dur']
    gap = o.gap if o.gap is not None else brand().get('pause_gap', 0.15)
    # in a voiceover every long-ish pause can go; on camera a tiny pause cut is a visible jump, so only cut real pauses
    min_pause = o.min_pause if o.min_pause is not None else (0.4 if is_video else gap)

    print('transcribing...')
    words = transcribe(audio)
    drop = set() if o.keep_fillers else {i for i, w in enumerate(words) if norm(w['w']) in FILLERS}
    if not o.keep_retakes:
        drop |= retakes(words)
    ranges = keep_ranges(load(audio, SR), words, drop, gap, min_pause)
    new_words = remap(words, drop, ranges)
    out_sec = sum(b - a for a, b in ranges)

    if is_video:
        clips = [{'src': str(src).replace('\\', '/'), 'in': round(a + o.start, 3), 'dur': round(b - a, 3), 'audio': True,
                  'zoom': 1.0 if k % 2 == 0 else 1.08} for k, (a, b) in enumerate(ranges)]  # punch in on every other cut
    else:
        x = load(audio, 48000)
        f = int(0.01 * 48000)
        ramp = np.linspace(0, 1, f, dtype=np.float32)
        pieces = []
        for a, b in ranges:  # 10 ms fades at every join so no click and no clipped word tail
            p = x[int(a * 48000):int(b * 48000)].copy()
            if len(p) > 2 * f:
                p[:f] *= ramp
                p[-f:] *= ramp[::-1]
            pieces.append(p)
        y = np.concatenate(pieces)
        r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', '48000', '-ac', '1', '-i', '-',
                            '-af', 'highpass=f=70,acompressor=threshold=-20dB:ratio=2:attack=5:release=120:makeup=1',
                            '-c:a', 'pcm_s16le', str(d / 'voice.wav')], input=y.tobytes(), capture_output=True)
        if r.returncode:
            raise SystemExit(r.stderr.decode()[:300])

    (d / 'words.json').write_text(json.dumps(new_words, indent=0, ensure_ascii=False), encoding='utf-8')
    (d / 'transcript.txt').write_text(' '.join(f'[{w["w"]}]' if i in drop else w['w'] for i, w in enumerate(words)), encoding='utf-8')
    (d / 'pace.json').write_text(json.dumps({'src': str(src), 'gap': gap, 'min_pause': min_pause, 'in_sec': info['dur'],
                                             'out_sec': round(out_sec, 3), 'ranges': ranges}, indent=1), encoding='utf-8')
    edit = d / 'edit.json'
    if not edit.exists():
        edit.write_text(json.dumps({
            'voice': None if is_video else 'voice.wav',
            'clips': clips if is_video else [],
            'broll': [], 'hook': None, 'moments': [], 'captions': True, 'progress': False, 'music': None,
        }, indent=1, ensure_ascii=False), encoding='utf-8')
        note = 'starter edit.json written'
    else:
        note = 'edit.json already exists and was NOT changed: timings moved, so update its clips' + (' (new cut list in pace.json)' if is_video else '')
    cut = [words[i]['w'] for i in sorted(drop)]
    print(f'{info["dur"]:.1f}s -> {out_sec:.1f}s, {len(ranges) - 1} cuts, removed words: {" ".join(cut) or "none"}')
    print(f'{"jump-cut video" if is_video else "voice.wav"}, words.json, transcript.txt -> public/{o.slug}/ ; {note}')


if __name__ == '__main__':
    main()
