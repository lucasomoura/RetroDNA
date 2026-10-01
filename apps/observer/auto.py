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
    
    # Converte para caminho absoluto e substitui contra-barras por barras normais
    abs_out_path = Path(out_file).resolve().as_posix()
    
    for k, v in {
        "__OUT__": abs_out_path,
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
            Path(d) / "retrodna_observer.lua",
            out_file,
            mode=mode,
            seconds=seconds,
            seed=seed,
            skip_title=skip_title,
        )
        cmd = [
            mesen,
            "--luaScript",
            str(lua),
            str(Path(rom).resolve()),
            "--doNotSaveSettings",
            "--allowLuaScriptIO",  # Habilita acesso I/O do Lua sem pedir confirmação na GUI
        ]
        try:
            r = subprocess.run(
                cmd,
                timeout=timeout or seconds * 6 + 120,
                capture_output=True,
                text=True,
                check=False,
                cwd=str(Path(mesen).parent),  # Define a pasta do Mesen como CWD
            )
            code = r.returncode
            if code != 0:
                print(f"\n--- STDOUT MESEN (Code {code}) ---\n{r.stdout}")
                print(f"--- STDERR MESEN ---\n{r.stderr}")
        except subprocess.TimeoutExpired:
            code = None
    if not Path(out_file).exists() or Path(out_file).stat().st_size < 1000:
        raise RuntimeError(
            f"o Mesen não gravou dados em {out_file} (código {code}). Verifique a ROM, o caminho do Mesen e o acesso a I/O."
        )
    return out_file

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Executa o Mesen com o observador Lua."
    )
    parser.add_argument("--rom", required=True, help="Caminho para a ROM")
    parser.add_argument("--mesen", help="Caminho para o executável do Mesen")
    parser.add_argument(
        "--out", default="output.json", help="Arquivo de saída das métricas"
    )
    parser.add_argument(
        "--seconds",
        type=int,
        default=300,
        help="Duração em segundos (padrão: 300)",
    )
    parser.add_argument(
        "--mode", default="bot", help="Modo de execução (padrão: bot)"
    )
    parser.add_argument(
        "--seed", type=int, default=1, help="Seed para o bot (padrão: 1)"
    )

    args = parser.parse_args()

    # Busca o executável do Mesen se não for passado explicitamente
    mesen_bin = find_mesen(args.mesen)

    print(f"Iniciando sessão com o Mesen: {mesen_bin}")
    print(f"ROM: {args.rom}")
    print(f"Gravando métricas em: {args.out} ({args.seconds}s)...")

    run_session(
        mesen=mesen_bin,
        rom=args.rom,
        out_file=args.out,
        seconds=args.seconds,
        mode=args.mode,
        seed=args.seed,
    )

    print("Sessão concluída com sucesso!")