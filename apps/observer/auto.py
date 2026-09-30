"""Extração automatizada: roda o Mesen (modo --testRunner, sem interface) com o observador Lua."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TEMPLATE = Path(__file__).parent / "templates" / "retrodna_observer.lua"


def find_mesen(explicit=None):
    cands = [
        explicit,
        os.environ.get("RETRODNA_MESEN"),
        shutil.which("Mesen"),
        shutil.which("Mesen.exe"),
        "Mesen.exe",
        "./Mesen",
        "./Mesen.exe",
    ]
    for c in cands:
        if c and Path(c).is_file():
            return str(Path(c).resolve())
    raise FileNotFoundError(
        "Mesen não encontrado. Baixe o MesenCE (github.com/nesdev-org/MesenCE/releases) e passe --mesen CAMINHO."
    )


def render(out_file, mode="bot", seconds=300, seed=1, skip_title=True):
    s = TEMPLATE.read_text(encoding="utf-8")
    for k, v in {
        "__OUT__": str(Path(out_file).resolve()).replace("\\", "/"),
        "__MODE__": mode,
        "__SECONDS__": str(int(seconds)),
        "__SEED__": str(int(seed)),
        "__SKIP__": "true" if skip_title else "false",
    }.items():
        s = s.replace(k, v)
    return s


def prepare(lua_path, out_file, **kw):
    Path(lua_path).parent.mkdir(parents=True, exist_ok=True)
    Path(lua_path).write_text(render(out_file, **kw), encoding="utf-8")
    return lua_path


def run_session(
    mesen, rom, out_file, seconds=300, seed=1, mode="bot", skip_title=True, timeout=None
):
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        lua = prepare(
            Path(d) / "observer.lua",
            out_file,
            mode=mode,
            seconds=seconds,
            seed=seed,
            skip_title=skip_title,
        )
        cmd = [
            mesen,
            "--testRunner",
            str(lua),
            str(Path(rom).resolve()),
            "--doNotSaveSettings",
        ]
        try:
            r = subprocess.run(
                cmd,
                timeout=timeout or seconds * 6 + 120,
                capture_output=True,
                text=True,
                check=False,
            )
            code = r.returncode
        except subprocess.TimeoutExpired:
            code = None
            print(
                f"aviso: sessão excedeu o tempo; usando o que foi gravado em {out_file}",
                file=sys.stderr,
            )
    if not Path(out_file).exists() or Path(out_file).stat().st_size < 1000:
        raise RuntimeError(
            f"o Mesen não gravou dados em {out_file} (código {code}). Verifique a ROM, o caminho do Mesen e o acesso a I/O."
        )
    return out_file
