# Not Geese

Unofficial Polish translations of indie games, made with machine assistance and reviewed
in game by a human. Players download packages from [notgeese.cc](https://notgeese.cc).

This repo holds translation sources, build tools, player guides and the site. Game files are
never committed: builds read the player's own installed copy and output to ignored folders.

## Layout

```
AGENTS.md              how the work is done: workflow, delivery rules, conventions
docs/                  decisions.md, workspace.md (review panel), design.md (site)
games/catalog.yaml     translation status per game
games/<slug>/
  README.md            player install guide (Polish, shown on the site)
  game.yaml            version, coverage, test status, download
  docs/technical.md    engine, text format, build, test state
  docs/decisions.md    translation direction, terms, review outcome
  docs/INSTALL*.txt    player readme packed as READ-ME.txt (Polish)
  translations/        en-pl-review.json (the translation), bible.yaml, structure.yaml
  tools/, plugin/      extraction, build, runtime plugin
tools/                 shared: translation file, delta patches + applier, corrections, keyart
site/                  Astro site and the /admin/ review panel
supabase/              review panel backend
```

## How translations ship

A runtime plugin (BepInEx for Unity, overlay pak for Unreal) adds Polish without touching game
files. Where that's impossible, a delta patch carries only our difference and a small applier
rebuilds the file from the player's copy. Packages never contain the publisher's assets.

## Building

Python 3.11 and the original game installed:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe games/shotgun-cop-man/tools/build_plugin.py --game "C:/SteamLibrary/steamapps/common/Shotgun Cop Man"
```

Each game's `docs/technical.md` has its exact command. Builds write to the game's `dist/`,
never to the installation.

## License

Game names, original text and characters belong to their creators. These translations are
unofficial and not affiliated with or endorsed by the studios. The [MIT license](LICENSE) covers
this repository's translation text, tools and documentation. Bundled BepInEx is LGPL-2.1
(sources published next to the packages).
