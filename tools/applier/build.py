"""Builds notgeesePatch.exe, the patch applier added to delta packages.

Output goes to `tools/applier/bin/` (git-ignored). `tools/patch.py release`
calls this script itself when the .exe is missing or older than the source or icon,
and puts it in the package as `<Name>-PL-<version>.exe`. The icon `icon.ico` is the
site logo (`site/public/favicon.svg`) at 16–256 px.

    .venv\\Scripts\\python.exe tools\\applier\\build.py
"""

from __future__ import annotations

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'notgeesePatch.cs'
ICON = HERE / 'icon.ico'
OUT = HERE / 'bin' / 'notgeesePatch.exe'

COMPILERS = [
    Path(r'C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/Roslyn/csc.exe'),
    Path(r'C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe'),
]
FRAMEWORK = Path(r'C:/Windows/Microsoft.NET/Framework64/v4.0.30319')


def compiler() -> Path:
    for candidate in COMPILERS:
        if candidate.exists():
            return candidate
    raise SystemExit('C# compiler (csc.exe) not found.')


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(compiler()),
        '/nologo',
        '/target:exe',
        '/platform:anycpu',
        '/optimize+',
        '/langversion:5',
        '/codepage:65001',
        f'/win32icon:{ICON}',
        f'/r:{FRAMEWORK / "System.Windows.Forms.dll"}',
        f'/out:{OUT}',
        str(SOURCE),
    ]
    subprocess.run(command, check=True)
    print(f'{OUT} ({OUT.stat().st_size} B)')


if __name__ == '__main__':
    main()
