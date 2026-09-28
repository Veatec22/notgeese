"""Game covers, galleries and metadata from Steam.

For each game in `games/<game>/game.yaml`, fetches the store capsule from Steam
(art with logo, 616×353 or 1232×706) and selected screenshots, then saves
them to `site/public/keyart/<slug>/` as AVIF with a WebP fallback:

    cover-<width>.avif/.webp    tile cover and first panel slide
    shot-<n>-1600.avif/.webp    panel carousel slides, 16:9 crop

Which screenshots go into the gallery is set by `gallery` in game.yaml (numbers from
`--list-shots`, in slide order); without it the first five are used.
Also fills `steam_appid`, `year`, `gallery` and the store link in game.yaml.

    .venv\\Scripts\\python.exe tools\\keyart.py --game otxo          one game
    .venv\\Scripts\\python.exe tools\\keyart.py --all                all games
    .venv\\Scripts\\python.exe tools\\keyart.py --list-shots otxo    screenshot preview

Images are kept in the repo, never hotlinked from Steam. Capsules and screenshots
are the developers' promotional material; we use them to illustrate the translation
page, not as our own material.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
GAMES = ROOT / 'games'
KEYART = ROOT / 'site' / 'public' / 'keyart'

SHOT_WIDTH, SHOT_HEIGHT = 1600, 900
COVER_RATIO = 616 / 353
GALLERY_DEFAULT = 5
# Quality (AVIF, WebP) picked by eye on a few games. The cover has a logo and small text,
# so it gets more; screenshots at AVIF 40 lose only the finest texture and weigh
# 80–100 KB instead of 150+. WebP is the fallback for old browsers, so it can be weaker.
COVER_QUALITY, SHOT_QUALITY = (55, 78), (40, 60)

SEARCH = 'https://steamcommunity.com/actions/SearchApps/{}'
DETAILS = 'https://store.steampowered.com/api/appdetails?appids={}&l=english'
STORE = 'https://store.steampowered.com/app/{}/'
ASSETS = 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{}/'
USER_AGENT = 'notgeese-keyart/2.0 (+https://github.com/Veatec22/notgeese)'
# Without these cookies some store pages show an age gate instead of art.
STORE_COOKIES = 'birthtime=0; wants_mature_content=1; lastagecheckage=1-0-1990'


def fetch(url: str, cookies: str | None = None) -> bytes:
    headers = {'User-Agent': USER_AGENT}
    if cookies:
        headers['Cookie'] = cookies
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def try_fetch(url: str) -> bytes | None:
    try:
        return fetch(url)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def normalise(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '', name.lower())


def find_appid(title: str) -> int | None:
    """Steam also returns sequels and demos, so an exact name wins."""
    results = json.loads(fetch(SEARCH.format(urllib.parse.quote(title))))
    if not results:
        return None

    wanted = normalise(title)
    for entry in results:
        if normalise(entry['name']) == wanted:
            return int(entry['appid'])
    return int(results[0]['appid'])


def app_details(appid: int) -> dict:
    payload = json.loads(fetch(DETAILS.format(appid)))
    # Some games (I Am Your Beast) come back under a different key than the requested appid.
    entry = payload.get(str(appid)) or (next(iter(payload.values())) if len(payload) == 1 else {})
    if not entry.get('success'):
        raise RuntimeError(f'Steam returned no data for appid {appid}')
    return entry['data']


def capsule_urls(appid: int, details: dict) -> list[str]:
    """Cover candidates, best first.

    Newer games keep the capsule under a hashed path the API does not give;
    only the store page knows it. Older ones use a plain path. The `_2x` version
    does not always exist. Last fallback is `header.jpg` (460×215, wider crop).
    """
    base = ASSETS.format(appid)
    found = [f'{base}capsule_616x353.jpg']
    try:
        page = fetch(STORE.format(appid), cookies=STORE_COOKIES).decode('utf-8', 'replace')
        # The store serves URLs from different CDNs (akamai, fastly); take the path only.
        match = re.search(rf'/steam/apps/{appid}/([^"\s?]*?capsule_616x353\.jpg)', page)
        if match and base + match.group(1) not in found:
            found.insert(0, base + match.group(1))
    except urllib.error.URLError:
        pass

    urls = []
    for url in found:
        urls += [url.replace('capsule_616x353.jpg', 'capsule_616x353_2x.jpg'), url]
    return urls + [(details.get('header_image') or f'{base}header.jpg').split('?')[0]]


def crop_to(image: Image.Image, ratio: float) -> Image.Image:
    """Centered crop to the given ratio, no distortion."""
    width, height = image.size
    if width / height > ratio:
        crop = round(height * ratio)
        left = (width - crop) // 2
        return image.crop((left, 0, left + crop, height))
    crop = round(width / ratio)
    top = (height - crop) // 2
    return image.crop((0, top, width, top + crop))


def save(image: Image.Image, stem: Path, quality: tuple[int, int]) -> None:
    image.save(stem.with_name(f'{stem.name}.avif'), 'AVIF', quality=quality[0], speed=4)
    image.save(stem.with_name(f'{stem.name}.webp'), 'WEBP', quality=quality[1], method=6)


def save_cover(raw: bytes, folder: Path) -> str:
    """Capsule at native width, plus a 616 px variant for phones from the 2× version."""
    image = Image.open(io.BytesIO(raw)).convert('RGB')
    if abs(image.width / image.height - COVER_RATIO) > 0.02:
        image = crop_to(image, COVER_RATIO)  # header.jpg is wider than the tile

    sizes = [616, 1232] if image.width >= 1232 else [min(image.width, 616)]
    for size in sizes:
        scaled = image.resize((size, round(size / COVER_RATIO)), Image.LANCZOS)
        save(scaled, folder / f'cover-{size}', COVER_QUALITY)
    return f'{image.width}×{image.height}'


def save_shot(raw: bytes, folder: Path, number: int) -> None:
    image = crop_to(Image.open(io.BytesIO(raw)).convert('RGB'), SHOT_WIDTH / SHOT_HEIGHT)
    save(image.resize((SHOT_WIDTH, SHOT_HEIGHT), Image.LANCZOS), folder / f'shot-{number}-{SHOT_WIDTH}', SHOT_QUALITY)


def set_scalar(text: str, key: str, value: str) -> str:
    """Replaces a top-level key's value, keeping the rest of the file."""
    pattern = re.compile(rf'^{re.escape(key)}:.*$', re.MULTILINE)
    line = f'{key}: {value}'
    return pattern.sub(line, text) if pattern.search(text) else f'{text.rstrip()}\n{line}\n'


def set_store(text: str, url: str) -> str:
    """Sets the Steam link without touching other stores (e.g. GOG) in `stores`."""
    block = f'stores:\n  steam: {url}'
    if re.search(r'^stores:\s*\{\s*\}\s*$', text, re.MULTILINE):
        return re.sub(r'^stores:\s*\{\s*\}\s*$', block, text, flags=re.MULTILINE)
    if re.search(r'^  steam:.*$', text, re.MULTILINE):
        return re.sub(r'^  steam:.*$', f'  steam: {url}', text, count=1, flags=re.MULTILINE)
    if re.search(r'^stores:\s*$', text, re.MULTILINE):
        return re.sub(r'^stores:\s*$', block, text, count=1, flags=re.MULTILINE)
    return f'{text.rstrip()}\n{block}\n'


def process(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    data = yaml.safe_load(text)
    slug = data['slug']

    appid = data.get('steam_appid') or find_appid(data['title'])
    if not appid:
        print(f'{slug}: game not found on Steam; fill steam_appid by hand')
        return

    details = app_details(appid)
    screenshots = [item['path_full'] for item in details.get('screenshots', [])]
    gallery = data.get('gallery') or list(range(1, min(GALLERY_DEFAULT, len(screenshots)) + 1))
    gallery = [number for number in gallery if 1 <= number <= len(screenshots)]

    # The folder is built alongside and replaces the old one only at the end, so an
    # interrupted download never leaves a game with half a gallery.
    folder = KEYART / f'.{slug}.tmp'
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)

    cover = 'none, placeholder tile stays'
    for url in capsule_urls(appid, details):
        raw = try_fetch(url)
        if raw:
            cover = f'{save_cover(raw, folder)} from {url.rsplit("/", 1)[-1]}'
            break
    for number in gallery:
        save_shot(fetch(screenshots[number - 1]), folder, number)

    target = KEYART / slug
    shutil.rmtree(target, ignore_errors=True)
    folder.rename(target)
    for old in (KEYART / f'{slug}.webp', KEYART / f'{slug}.jpg'):
        old.unlink(missing_ok=True)  # files from before covers and galleries

    size = sum(file.stat().st_size for file in target.iterdir()) / 1024
    print(f'{slug}: cover {cover}, gallery {gallery} of {len(screenshots)}, {size:.0f} KB (appid {appid})')

    text = set_scalar(text, 'steam_appid', str(appid))
    text = set_scalar(text, 'gallery', '[' + ', '.join(map(str, gallery)) + ']')
    released = re.search(r'\b(19|20)\d{2}\b', (details.get('release_date') or {}).get('date', ''))
    if released:
        text = set_scalar(text, 'year', released.group(0))
    text = set_store(text, STORE.format(appid))
    path.write_text(text, encoding='utf-8')


def list_shots(path: Path) -> None:
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    appid = data.get('steam_appid') or find_appid(data['title'])
    if not appid:
        print('game not found on Steam')
        return
    for number, item in enumerate(app_details(appid).get('screenshots', []), start=1):
        print(f'{number:2}  {item["path_full"]}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--game', help='slug of one game')
    target.add_argument('--all', action='store_true', help='refresh all games')
    target.add_argument('--list-shots', metavar='SLUG', help='list available screenshots and exit')
    args = parser.parse_args()

    if args.list_shots:
        list_shots(GAMES / args.list_shots / 'game.yaml')
        return 0

    paths = sorted(GAMES.glob('*/game.yaml'))
    if args.game:
        paths = [path for path in paths if path.parent.name == args.game]
        if not paths:
            print(f'no game {args.game}')
            return 1

    for number, path in enumerate(paths):
        if number:
            time.sleep(1)  # Steam dislikes rapid-fire requests.
        try:
            process(path)
        except Exception as error:  # one game must not break the whole run
            print(f'{path.parent.name}: {error}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
