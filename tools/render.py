"""Render the final video and check it.

    py -3.12 tools/render.py <video-name>

prep -> Remotion render -> loudness set to -14 LUFS (what TikTok / Reels / Shorts play at) -> automatic checks.
Output: out/<name>/<name>.mp4, checks.txt and sheet.jpg (one frame per second, for a quick look).
If brand.json has an output_folder (e.g. on OneDrive), the mp4 and post.txt are copied there too.
"""
import math
import re
import shutil
import sys
import time

import prep
from common import ROOT, brand, probe, run

TARGET = -14.0


def lufs(path):
    e = run(['ffmpeg', '-hide_banner', '-i', path, '-map', '0:a:0', '-af', 'ebur128', '-f', 'null', '-']).stderr
    m = re.findall(r'I:\s+(-?[\d.]+|-inf) LUFS', e)
    return float(m[-1]) if m and m[-1] != '-inf' else None


def checks(path, dur):
    """Problems a viewer would notice. Returns (problems, warnings)."""
    bad, warn = [], []
    p = probe(path)
    if (p.get('w'), p.get('h')) != (1080, 1920):
        bad.append(f"size is {p.get('w')}x{p.get('h')}, should be 1080x1920")
    if round(p.get('fps', 0)) != 30:
        bad.append(f"{p.get('fps')} fps, should be 30")
    if not p['audio']:
        bad.append('no sound')
    loud = lufs(path) if p['audio'] else None
    if p['audio'] and loud is None:
        bad.append('sound is silent')
    elif loud is not None and abs(loud - TARGET) > 1.5:
        warn.append(f'loudness {loud:.1f} LUFS (aim {TARGET})')
    v = run(['ffmpeg', '-hide_banner', '-i', path, '-vf', 'blackdetect=d=0.2:pix_th=0.08,freezedetect=n=0.002:d=1.5', '-an', '-f', 'null', '-']).stderr
    for a, b in re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', v):
        bad.append(f'black screen {float(a):.1f}-{float(b):.1f}s')
    for a in re.findall(r'freeze_start: ([\d.]+)', v):
        warn.append(f'picture stands still for 1.5s+ from {float(a):.1f}s (fine if intended)')
    a = run(['ffmpeg', '-hide_banner', '-i', path, '-af', 'silencedetect=n=-40dB:d=0.8', '-vn', '-f', 'null', '-']).stderr
    for s, e in zip(re.findall(r'silence_start: ([\d.]+)', a), re.findall(r'silence_end: ([\d.]+)', a)):
        warn.append(f'no sound {float(s):.1f}-{float(e):.1f}s')
    if not 3 <= dur <= 180:
        warn.append(f'{dur:.0f}s long: Shorts allow up to 3 min, most short videos land at 15-60s')
    return bad, warn, loud


def main(slug):
    prep.main(slug)
    out = ROOT / 'out' / slug
    out.mkdir(parents=True, exist_ok=True)
    raw, final = out / 'render-raw.mp4', out / f'{slug}.mp4'
    t0 = time.time()
    npx = shutil.which('npx') or 'npx'
    r = run([npx, 'remotion', 'render', 'src/index.ts', slug, raw, '--log=error', '--crf=18'], cwd=ROOT)
    if r.returncode:
        sys.exit(f'render failed:\n{(r.stderr or r.stdout)[-1500:]}')
    # static gain to the platforms' loudness, then a limiter so peaks never clip; the picture is copied untouched
    loud = lufs(raw)
    gain = TARGET - loud if loud is not None else 0
    r = run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-c:v', 'copy', '-af', f'volume={gain:.2f}dB,alimiter=limit=0.89:level=false',
             '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', final])
    if r.returncode:
        sys.exit(f'loudness step failed: {r.stderr[:300]}')
    raw.unlink()
    dur = probe(final)['dur']
    run(['ffmpeg', '-v', 'error', '-y', '-i', final, '-vf', f'fps=1,scale=180:-2,tile=8x{math.ceil(dur / 8)}', '-frames:v', '1', out / 'sheet.jpg'])
    bad, warn, after = checks(final, dur)
    lines = [f'{slug}.mp4: {dur:.1f}s, rendered in {time.time() - t0:.0f}s, loudness {after if after is None else round(after, 1)} LUFS']
    lines += [f'PROBLEM: {b}' for b in bad] + [f'check: {w}' for w in warn]
    lines.append('all checks passed' if not bad and not warn else f'{len(bad)} problems, {len(warn)} things to look at')
    (out / 'checks.txt').write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines) + f'\n-> out/{slug}/')
    dest = brand().get('output_folder')
    if dest and not bad:
        from pathlib import Path
        Path(dest).mkdir(parents=True, exist_ok=True)
        for f in (final, out / 'post.txt'):
            if f.exists():
                shutil.copy2(f, Path(dest) / f.name)
        print(f'copied to {dest}')
    return not bad


if __name__ == '__main__':
    sys.exit(0 if main(sys.argv[1]) else 1)
