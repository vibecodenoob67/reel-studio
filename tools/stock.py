"""Free upright stock B-roll from Pexels (free to use, no credit needed) when his own footage has nothing that fits.

    py -3.12 tools/stock.py "man tying running shoes" [how many, default 3]

Downloads into library/stock/ and adds them to the catalog. Needs a free Pexels API key in .env:
    PEXELS_API_KEY=xxxxxxxx      (get one at https://www.pexels.com/api/ -> "Get started")
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from common import ROOT
from index import run_index

STOCK = ROOT / 'library' / 'stock'


def key():
    k = os.environ.get('PEXELS_API_KEY')
    env = ROOT / '.env'
    if not k and env.exists():
        m = re.search(r'^PEXELS_API_KEY\s*=\s*(\S+)', env.read_text(encoding='utf-8'), re.M)
        k = m and m.group(1).strip('"\'')
    if not k:
        sys.exit('No Pexels key yet. Get a free one at https://www.pexels.com/api/ and put this line in .env:\nPEXELS_API_KEY=your-key')
    return k


def get(url, k=None):
    req = urllib.request.Request(url, headers={'User-Agent': 'reel-studio', **({'Authorization': k} if k else {})})
    return urllib.request.urlopen(req, timeout=60)


def main(query, n=3):
    k = key()
    url = 'https://api.pexels.com/videos/search?' + urllib.parse.urlencode({'query': query, 'orientation': 'portrait', 'per_page': n})
    try:
        videos = json.load(get(url, k)).get('videos', [])
    except urllib.error.HTTPError as e:
        sys.exit('Pexels refused the key (check .env)' if e.code in (401, 403) else f'Pexels error {e.code}')
    if not videos:
        sys.exit(f'nothing found for "{query}": try simpler words')
    STOCK.mkdir(parents=True, exist_ok=True)
    tag = re.sub(r'[^a-z0-9]+', '-', query.lower()).strip('-')[:40]
    for v in videos:
        files = [f for f in v['video_files'] if f.get('file_type') == 'video/mp4' and f.get('height')]
        # closest to full HD upright, never tiny
        f = min(files, key=lambda f: (f['height'] < 1280, abs(f['height'] - 1920)))
        out = STOCK / f"{tag}-{v['id']}.mp4"
        if not out.exists():
            part = out.with_suffix('.part')
            with get(f['link']) as r, open(part, 'wb') as w:
                while chunk := r.read(1 << 20):
                    w.write(chunk)
            part.replace(out)
        print(f"{out.name}  {f['width']}x{f['height']}  {v['duration']}s  by {v.get('user', {}).get('name', '?')}")
    run_index([STOCK])


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3)
