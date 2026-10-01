"""Lançamento do Mesen (apps/observer/auto.py) e do observador Lua, sem precisar do Mesen real."""

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
from test_oam import make_trace

from apps.observer import auto
from packages.schema import OamSample

FAKE = """
import json, re, shutil, sys, time
args = sys.argv[1:]
json.dump(args, open({argv!r}, "w"))
lua = next(a for a in args if a.endswith(".lua"))
out = re.search(r'out = "([^"]*)"', open(lua, encoding="utf-8").read()).group(1)
if {mode!r} == "ok":
    shutil.copy({trace!r}, out)
    open(out + ".done", "w").write("ok")
time.sleep(60)
"""


@pytest.fixture(scope="module")
def trace(tmp_path_factory):
    path = tmp_path_factory.mktemp("trace") / "t.jsonl"
    make_trace(str(path), seconds=60)
    return path


def fake_mesen(tmp_path, mode, trace):
    script = tmp_path / "fake_mesen.py"
    argv = tmp_path / "argv.json"
    script.write_text(FAKE.format(argv=str(argv), mode=mode, trace=str(trace)))
    return [sys.executable, str(script)], argv


@pytest.mark.parametrize("runner", auto.RUNNERS)
def test_session_finishes_on_done_marker_and_closes_mesen(tmp_path, trace, runner):
    mesen, argv = fake_mesen(tmp_path, "ok", trace)
    rom = tmp_path / "jogo.sfc"
    rom.write_bytes(b"x")
    out = tmp_path / "s" / "sessao1.oam.jsonl"
    t0 = time.monotonic()
    auto.run_session(mesen, rom, out, seconds=60, runner=runner)
    assert time.monotonic() - t0 < 30  # não esperou o "Mesen" (que dorme 60 s)
    assert out.stat().st_size > 1000
    args = json.loads(argv.read_text())
    flags = {a for a in args if a.startswith("--")}
    assert flags <= auto.KNOWN_FLAGS  # nada de --luaScript / --allowLuaScriptIO
    assert ("--testRunner" in flags) == (runner == "testrunner")
    assert any(a.endswith("jogo.sfc") for a in args)


def test_silent_mesen_raises_with_io_hint(tmp_path, trace):
    mesen, _ = fake_mesen(tmp_path, "silent", trace)
    out = tmp_path / "sessao.jsonl"
    out.write_text("dados antigos de outra sessão" * 100)
    with pytest.raises(RuntimeError, match="Allow access to I/O"):
        auto.run_session(mesen, tmp_path / "x.sfc", out, seconds=10, start_timeout=1)
    assert not out.exists()  # sessão antiga não é reaproveitada


def test_observer_uses_only_documented_mesen_api():
    src = (
        Path(auto.__file__).parent / "templates" / "retrodna_observer.lua"
    ).read_text(encoding="utf-8")
    events = set(re.findall(r"emu\.eventType\.(\w+)", src))
    assert events <= {"inputPolled", "endFrame", "scriptEnded", "startFrame"}, events
    assert set(re.findall(r"emu\.memType\.(\w+)", src)) == {"snesSpriteRam"}
    funcs = set(re.findall(r"emu\.(\w+)\(", src))
    documented = {"log", "displayMessage", "read", "getInput", "setInput", "getState"}
    documented |= {"stop", "exit", "addEventCallback"}
    assert funcs <= documented, funcs - documented


LUA = shutil.which("lua5.4") or shutil.which("lua")


@pytest.mark.skipif(LUA is None, reason="interpretador Lua não instalado")
def test_observer_runs_against_mocked_mesen(tmp_path):
    out = tmp_path / "o.jsonl"
    lua = auto.prepare(tmp_path / "obs.lua", out, mode="bot", seconds=4, seed=3)
    mock = Path(__file__).parent / "fixtures" / "mock_emu.lua"
    r = subprocess.run(
        [LUA, str(mock), str(lua)], capture_output=True, text=True, check=False
    )
    assert r.returncode == 0, r.stderr
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert rows[0]["meta"]["source"] == "oam"
    assert len(rows) == 1 + 4 * 60 // 6
    for row in rows[1:]:
        OamSample.model_validate(row)
    assert Path(f"{out}.done").exists()
    assert "snes.ppu.layers[0].hScrollLatch" not in rows[1]["sc"]


@pytest.mark.skipif(LUA is None, reason="interpretador Lua não instalado")
def test_observer_degrades_gracefully_without_io(tmp_path):
    out = tmp_path / "o.jsonl"
    lua = auto.prepare(tmp_path / "obs.lua", out, mode="bot", seconds=2, seed=3)
    mock = Path(__file__).parent / "fixtures" / "mock_emu.lua"
    env = {"NO_IO": "1", "PATH": ""}
    r = subprocess.run(
        [LUA, str(mock), str(lua)], capture_output=True, text=True, env=env, check=False
    )
    assert r.returncode == 0, r.stderr
    assert "I/O" in r.stdout and not out.exists()
