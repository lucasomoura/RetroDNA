"""Extração automatizada: abre o Mesen com a ROM e o observador Lua; o bot joga sozinho."""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

TEMPLATE = Path(__file__).parent / "templates" / "retrodna_observer.lua"
START_TIMEOUT = (
    45  # s: sem arquivo de saída depois disso => ROM/script/I-O não funcionaram
)
RUNNERS = ("gui", "testrunner")
# Opções de linha de comando que o MesenCE realmente aceita (conferido no binário 2.2.1).
# Scripts .lua e a ROM entram como argumentos posicionais; não existem --luaScript nem
# --allowLuaScriptIO. O acesso a I/O é uma configuração do Mesen, não uma opção de CLI.
KNOWN_FLAGS = {"--doNotSaveSettings", "--enableStdout", "--testRunner"}
IO_HINT = (
    "Verifique no Mesen: Configurações > aba 'Script Window' > marque "
    "'Allow access to I/O and OS functions'."
)


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
        "Mesen não encontrado. Baixe o MesenCE "
        "(github.com/nesdev-org/MesenCE/releases) e passe --mesen CAMINHO."
    )


def render(out_file, mode="bot", seconds=300, seed=1, skip_title=True):
    s = TEMPLATE.read_text(encoding="utf-8")
    # caminho absoluto com barras normais (o Lua no Windows aceita)
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


def build_command(mesen, rom, lua, runner="gui"):
    """`mesen` pode ser um caminho ou uma lista (prefixo do comando; útil em testes)."""
    prefix = list(mesen) if isinstance(mesen, list | tuple) else [str(mesen)]
    rom, lua = str(Path(rom).resolve()), str(lua)
    if runner == "testrunner":
        return [
            *prefix,
            "--testRunner",
            lua,
            rom,
            "--doNotSaveSettings",
            "--enableStdout",
        ]
    return [*prefix, rom, lua, "--doNotSaveSettings", "--enableStdout"]


def _stop(proc):
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()


def _log_tail(path, n=12):
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-n:])


def run_session(
    mesen,
    rom,
    out_file,
    seconds=300,
    seed=1,
    mode="bot",
    skip_title=True,
    runner="gui",
    start_timeout=START_TIMEOUT,
    timeout=None,
):
    """Roda uma sessão. Espera o marcador `.done` do script e então fecha o Mesen.

    runner="gui": abre o Mesen normalmente com a ROM e o script como argumentos.
    runner="testrunner": usa `--testRunner` (modo headless anunciado pelo Mesen).
    A saída do Mesen (inclui as linhas `RDNA:` do script) vai para `<out>.mesen.log`.
    """
    out = Path(out_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    done, log = Path(f"{out}.done"), Path(f"{out}.mesen.log")
    for p in (out, done, log):
        p.unlink(missing_ok=True)
    limit = timeout or seconds * 6 + 120
    with tempfile.TemporaryDirectory() as d:
        lua = prepare(
            Path(d) / "retrodna_observer.lua",
            out,
            mode=mode,
            seconds=seconds,
            seed=seed,
            skip_title=skip_title,
        )
        cmd = build_command(mesen, rom, lua, runner)
        cwd = (
            Path(mesen).parent
            if isinstance(mesen, str | Path) and Path(mesen).is_file()
            else None
        )
        with open(log, "wb") as logf:
            proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, cwd=cwd)
            started = time.monotonic()
            try:
                while not done.exists() and proc.poll() is None:
                    elapsed = time.monotonic() - started
                    if not out.exists() and elapsed > start_timeout:
                        tail = _log_tail(log)
                        raise RuntimeError(
                            f"o Mesen não gravou nada em {start_timeout}s (runner={runner}). "
                            f"{IO_HINT} Se a ROM não abriu, tente --runner "
                            f"{'testrunner' if runner == 'gui' else 'gui'}."
                            + (f"\n--- log do Mesen ---\n{tail}" if tail else "")
                        )
                    if elapsed > limit:
                        break
                    time.sleep(0.3)
            finally:
                _stop(proc)
    if not out.exists() or out.stat().st_size < 1000:
        raise RuntimeError(
            f"sessão sem dados em {out_file}. {IO_HINT}\n{_log_tail(log)}"
        )
    return out_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Executa o Mesen com o observador Lua."
    )
    parser.add_argument("--rom", required=True, help="Caminho para a ROM")
    parser.add_argument("--mesen", help="Caminho para o executável do Mesen")
    parser.add_argument("--out", default="sessao.oam.jsonl", help="Arquivo de saída")
    parser.add_argument(
        "--seconds", type=int, default=300, help="Duração (padrão: 300)"
    )
    parser.add_argument("--mode", default="bot", choices=["bot", "human"])
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--runner", default="gui", choices=RUNNERS)
    args = parser.parse_args()

    mesen_bin = find_mesen(args.mesen)
    print(f"Iniciando sessão com o Mesen: {mesen_bin}\nROM: {args.rom}")
    print(f"Gravando em: {args.out} ({args.seconds}s)...")
    run_session(
        mesen_bin,
        args.rom,
        args.out,
        args.seconds,
        seed=args.seed,
        mode=args.mode,
        runner=args.runner,
    )
    print("Sessão concluída com sucesso!")
