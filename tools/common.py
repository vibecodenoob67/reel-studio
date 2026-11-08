# Shared helpers for the tools: settings, ffprobe, speech-to-text.
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')  # Windows console would choke on emoji / accents in transcripts

VIDEO_EXT = {'.mp4', '.mov', '.m4v', '.mkv', '.webm', '.avi'}
AUDIO_EXT = {'.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg', '.opus'}


def brand():
    p = ROOT / 'brand.json'
    if not p.exists():
        sys.exit('brand.json is missing: copy brand.example.json to brand.json and fill it in (Claude can do this).')
    return json.loads(p.read_text(encoding='utf-8'))


def video_dir(slug):
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', slug):
        sys.exit(f'bad video name "{slug}": use lowercase letters, numbers and dashes, like gym-tips-3')
    d = ROOT / 'public' / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def run(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding='utf-8', errors='replace', **kw)


def probe(path):
    """Length, size after phone rotation, fps, and whether there is sound. Raises if the file can't be read."""
    r = run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path])
    if r.returncode:
        raise RuntimeError(f'cannot read {path}: {r.stderr.strip()[:200]}')
    j = json.loads(r.stdout)
    st = j.get('streams', [])
    v = next((s for s in st if s['codec_type'] == 'video' and not s.get('disposition', {}).get('attached_pic')), None)
    out = {'dur': round(float(j['format'].get('duration') or 0), 3), 'audio': any(s['codec_type'] == 'audio' for s in st)}
    if v:
        w, h = v['width'], v['height']
        rot = int(float(v.get('tags', {}).get('rotate', 0) or 0))
        for sd in v.get('side_data_list', []):
            if 'rotation' in sd:
                rot = int(float(sd['rotation']))
        if abs(rot) % 180 == 90:  # phone footage stored sideways with a rotate flag
            w, h = h, w
        num, den = (v.get('avg_frame_rate') or '0/1').split('/')
        out.update(w=w, h=h, fps=round(float(num) / float(den), 2) if float(den) else 0)
    return out


_model = None
# a prompt full of fillers makes Whisper write the "um"s down instead of silently cleaning them up
FILLER_PROMPT = 'Umm, so, uh, I was like, hmm... okay. Uh, yeah, so, um.'


def transcribe(path):
    """Words with start/end seconds: [{'w': 'Hello', 's': 0.31, 'e': 0.62}, ...]. Runs on the CPU, free."""
    global _model
    from faster_whisper import WhisperModel
    if _model is None:
        _model = WhisperModel(brand().get('whisper_model', 'small.en'), device='cpu', compute_type='int8')
    segs, _ = _model.transcribe(str(path), word_timestamps=True, vad_filter=True, beam_size=5, initial_prompt=FILLER_PROMPT)
    return [{'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3)} for s in segs for w in (s.words or []) if w.word.strip()]
