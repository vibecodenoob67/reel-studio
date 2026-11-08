"""Turn public/<name>/edit.json (Claude's edit) into what the video template plays.

    py -3.12 tools/prep.py <video-name>

Checks the edit, cuts each used piece out of the original footage (cropped to upright 1080x1920, 30 fps, H.264 so
the browser preview can play iPhone HEVC too) into public/<name>/media/, and writes public/<name>/render.json.
The preview (npm run studio) reloads by itself when render.json changes. Unchanged pieces are not cut again.
"""
import hashlib
import json
import sys
from pathlib import Path

from common import ROOT, brand, probe, run, video_dir

FPS, W, H = 30, 1080, 1920
CAPTION_DEFAULTS = {'font': 'Montserrat', 'color': '#FFFFFF', 'highlight': '#FFD400', 'stroke': '#000000',
                    'size': 76, 'y': 0.6, 'uppercase': True}


def cut(d, c, audio):
    """One piece of footage -> media/<hash>.mp4 (exactly what's on screen). Returns the file name."""
    focus = min(1, max(0, c.get('focus', 0.5)))
    key = json.dumps([c['src'], round(c['in'], 3), round(c['dur'], 3), focus, audio])
    name = hashlib.sha1(key.encode()).hexdigest()[:12] + '.mp4'
    out = d / 'media' / name
    if out.exists():
        return name
    out.parent.mkdir(exist_ok=True)
    # crop to 9:16 (focus 0 = keep the left side, 1 = right side), then scale; 0.1 s spare so the clip never runs short
    vf = (f"crop='min(iw,ih*9/16)':'min(ih,iw*16/9)':'(iw-ow)*{focus}':'(ih-oh)/2',"
          f"scale={W}:{H}:flags=lanczos,setsar=1,fps={FPS}")
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', c['in'], '-i', c['src'], '-t', c['dur'] + 0.1, '-vf', vf,
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', 18, '-pix_fmt', 'yuv420p']
    fade = f"afade=t=in:d=0.015,afade=t=out:st={max(0, c['dur'] - 0.015):.3f}:d=0.015"  # no clicks at jump cuts
    cmd += ['-af', fade, '-c:a', 'aac', '-b:a', '192k', '-ar', 48000] if audio else ['-an']
    tmp = out.with_name(name + '.part.mp4')
    r = run(cmd + [tmp])
    if r.returncode:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"could not cut {c['src']}: {r.stderr.strip()[:300]}")
    tmp.replace(out)
    return name


def check(e, d):
    """Every mistake in the edit at once, in plain words."""
    errs, probes = [], {}
    for kind in ('clips', 'broll'):
        for i, c in enumerate(e.get(kind, [])):
            where = f'{kind}[{i}]'
            if not Path(c.get('src', '')).is_file():
                errs.append(f"{where}: file not found: {c.get('src')}")
                continue
            p = probes.setdefault(c['src'], probe(c['src']))
            if 'w' not in p:
                errs.append(f'{where}: not a video: {c["src"]}')
            if c.get('in', -1) < 0 or c.get('dur', 0) < 0.2:
                errs.append(f'{where}: needs "in" >= 0 and "dur" >= 0.2')
            elif c['in'] + c['dur'] > p['dur'] + 0.05:
                errs.append(f'{where}: asks for {c["in"]}-{c["in"] + c["dur"]:.2f}s but the file is only {p["dur"]}s long')
            if kind == 'broll' and 'at' not in c:
                errs.append(f'{where}: B-roll needs "at" (second in the final video where it appears)')
    if e.get('voice') and not (d / e['voice']).is_file():
        errs.append(f'voice file missing: public/{d.name}/{e["voice"]} (run tools/pace.py first)')
    if e.get('music') and not Path(e['music'].get('src', '')).is_file():
        errs.append(f'music file not found: {e["music"].get("src")}')
    return errs, probes


def main(slug):
    d = video_dir(slug)
    e = json.loads((d / 'edit.json').read_text(encoding='utf-8'))
    errs, probes = check(e, d)
    voice_dur = probe(d / e['voice'])['dur'] if e.get('voice') and not errs else 0
    clips_dur = sum(c['dur'] for c in e.get('clips', []))
    if voice_dur and clips_dur < voice_dur - 0.05:
        errs.append(f'clips cover {clips_dur:.2f}s but the voice is {voice_dur:.2f}s: add {voice_dur - clips_dur:.2f}s of clips')
    if not e.get('clips'):
        errs.append('no clips yet')
    if errs:
        sys.exit('edit.json has problems:\n- ' + '\n- '.join(errs))

    frames = lambda s: round(s * FPS)
    clips, t = [], 0
    for c in e['clips']:
        audio = bool(c.get('audio')) and probes[c['src']]['audio']
        a, b = frames(t), frames(t + c['dur'])
        clips.append({'file': f'{slug}/media/{cut(d, c, audio)}', 'from': a, 'frames': b - a, 'audio': audio, 'zoom': c.get('zoom', 1)})
        t += c['dur']
    broll = [{'file': f'{slug}/media/{cut(d, c, False)}', 'from': frames(c['at']), 'frames': frames(c['dur']),
              'zoom': c.get('zoom', 1)} for c in e.get('broll', [])]
    total = max(frames(t), frames(voice_dur), *[b['from'] + b['frames'] for b in broll], 1)
    if voice_dur:  # the voice decides the length: clips that run past it are trimmed
        total = frames(voice_dur)
        clips = [{**c, 'frames': min(c['frames'], total - c['from'])} for c in clips if c['from'] < total]

    music = None
    if e.get('music'):
        m = e['music']
        name = 'music-' + hashlib.sha1(m['src'].encode()).hexdigest()[:8] + '.m4a'
        if not (d / name).exists():
            r = run(['ffmpeg', '-v', 'error', '-y', '-i', m['src'], '-vn', '-c:a', 'aac', '-b:a', '192k', d / name])
            if r.returncode:
                sys.exit(f'could not read the music file: {r.stderr[:200]}')
        music = {'file': f'{slug}/{name}', 'volume': m.get('volume', 0.12)}

    words_file = d / 'words.json'
    r = {
        'id': slug, 'fps': FPS, 'width': W, 'height': H, 'frames': total,
        'voice': f'{slug}/{e["voice"]}' if e.get('voice') else None, 'music': music,
        'clips': clips, 'broll': broll,
        'words': json.loads(words_file.read_text(encoding='utf-8')) if words_file.exists() else [],
        'captions': e.get('captions', True), 'progress': e.get('progress', False),
        'hook': {'text': e['hook']['text'], 'frames': frames(e['hook'].get('dur', 2))} if e.get('hook') else None,
        'moments': [{**{k: v for k, v in m.items() if k not in ('at', 'dur')}, 'from': frames(m['at']), 'frames': frames(m.get('dur', 1.2))}
                    for m in e.get('moments', [])],
        'style': {**CAPTION_DEFAULTS, **brand().get('captions', {}), **e.get('style', {})},
    }
    (d / 'render.json').write_text(json.dumps(r, ensure_ascii=False), encoding='utf-8')
    used = {Path(c['file']).name for c in clips + broll}
    for f in (d / 'media').glob('*'):
        if f.name not in used:
            f.unlink()  # pieces from an earlier version of the edit
    print(f'{slug}: {total / FPS:.1f}s, {len(clips)} clips, {len(broll)} B-roll, {len(r["moments"])} moments -> public/{slug}/render.json')
    return r


if __name__ == '__main__':
    main(sys.argv[1])
