"""Catalog the footage folder(s) so Claude can choose clips without opening every video.

    py -3.12 tools/index.py            # folders from brand.json + library/stock
    py -3.12 tools/index.py D:/extra   # a different folder

For every video / audio file: length, upright or sideways, fps, has sound, a grid of still frames
(library/sheets/<id>.jpg, read left to right, top to bottom; sheet_times = the second each still was taken)
and what is said in it. Only new or changed files are processed; originals are never touched.
Result: library/index.json
"""
import hashlib
import json
import math
import sys
from pathlib import Path

from common import AUDIO_EXT, ROOT, VIDEO_EXT, brand, probe, run, transcribe

LIB = ROOT / 'library'
INDEX = LIB / 'index.json'


def sheet(path, dur, sid, upright):
    """A grid of still frames: one every ~2 s for short clips, sparser for long recordings, at most 36."""
    n = max(4, min(36, math.ceil(dur / (2 if dur <= 60 else 5))))
    step = dur / n
    cols = (8 if upright else 4) if n > 8 else 4
    out = LIB / 'sheets' / f'{sid}.jpg'
    out.parent.mkdir(parents=True, exist_ok=True)
    r = run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-vf',
             f'fps=1/{step:.3f},scale={"-2:320" if upright else "320:-2"},tile={cols}x{math.ceil(n / cols)}',
             '-frames:v', '1', '-q:v', '4', out])
    if r.returncode:
        raise RuntimeError(r.stderr.strip()[:200])
    return str(out.relative_to(ROOT)).replace('\\', '/'), [round(i * step, 1) for i in range(n)]


def speech(path):
    """What is said, as short timestamped lines ('[12.3] and that is why...'), or '' if nobody talks."""
    words, lines, cur = transcribe(path), [], []
    for w in words:
        if not cur:
            cur_s = w['s']
        cur.append(w['w'])
        if w['w'][-1:] in '.!?' or len(cur) >= 14:
            lines.append(f'[{cur_s:.1f}] ' + ' '.join(cur))
            cur = []
    if cur:
        lines.append(f'[{cur_s:.1f}] ' + ' '.join(cur))
    return '\n'.join(lines)


def run_index(folders):
    idx = json.loads(INDEX.read_text(encoding='utf-8')) if INDEX.exists() else {}
    seen, new = set(), []
    for folder in folders:
        folder = Path(folder)
        if not folder.exists():
            print(f'! folder not found: {folder}')
            continue
        for p in sorted(folder.rglob('*')):
            ext = p.suffix.lower()
            if ext not in VIDEO_EXT | AUDIO_EXT or not p.is_file():
                continue
            key = str(p.resolve()).replace('\\', '/')
            seen.add(key)
            stamp = f'{p.stat().st_size}-{int(p.stat().st_mtime)}'
            if idx.get(key, {}).get('stamp') == stamp:
                continue
            sid = hashlib.sha1(key.encode()).hexdigest()[:10]
            try:
                info = probe(p)  # on OneDrive this also downloads a cloud-only file, which can take a while
                e = {'stamp': stamp, 'id': sid, 'name': p.name, 'folder': str(p.parent).replace('\\', '/'), **info}
                if 'w' in info:
                    e['kind'] = 'video'
                    e['shape'] = 'upright' if info['h'] > info['w'] else 'sideways' if info['w'] > info['h'] else 'square'
                    e['sheet'], e['sheet_times'] = sheet(p, info['dur'], sid, info['h'] >= info['w'])
                else:
                    e['kind'] = 'audio'
                e['speech'] = speech(p) if info['audio'] else ''
            except Exception as ex:  # one broken file must not stop the whole catalog
                print(f'! skipped {p.name}: {ex}')
                continue
            idx[key] = e
            new.append(e)
            print(f"+ {e['kind']:5} {e['dur']:7.1f}s {e.get('shape', ''):8} {p.name}" + ('  (talking)' if e['speech'] else ''))
    scanned = [str(Path(f).resolve()).replace('\\', '/') for f in folders]
    for k in [k for k in idx if k not in seen and any(k.startswith(s + '/') for s in scanned)]:
        del idx[k]  # file was deleted or moved
    LIB.mkdir(exist_ok=True)
    INDEX.write_text(json.dumps(idx, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'{len(new)} new or changed, {len(idx)} files in the catalog -> library/index.json')
    return idx


if __name__ == '__main__':
    run_index(sys.argv[1:] or [*brand().get('footage_folders', []), ROOT / 'library' / 'stock'])
