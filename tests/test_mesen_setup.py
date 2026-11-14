import json

import pytest

from apps.cli import main
from apps.observer import mesen_setup


def write(path, data, bom=False):
    text = json.dumps(data)
    path.write_text(text, encoding="utf-8-sig" if bom else "utf-8")


def test_enables_io_and_makes_backup(tmp_path):
    p = tmp_path / "settings.json"
    write(
        p,
        {
            "Debug": {
                "ScriptWindow": {
                    "AllowIoOsAccess": False,
                    "AutoStartScriptOnLoad": False,
                    "X": 1,
                }
            }
        },
        bom=True,
    )
    changes = mesen_setup.enable_script_io(p)
    assert changes == {
        "AllowIoOsAccess": (False, True),
        "AutoStartScriptOnLoad": (False, True),
    }
    node = json.loads(p.read_text(encoding="utf-8"))["Debug"]["ScriptWindow"]
    assert node["AllowIoOsAccess"] is True and node["X"] == 1
    assert (tmp_path / "settings.json.bak").exists()
    assert mesen_setup.enable_script_io(p) == {}  # idempotente


def test_key_case_is_respected_and_missing_main_key_is_created(tmp_path):
    p = tmp_path / "settings.json"
    write(p, {"debug": {"scriptWindow": {}}})
    assert mesen_setup.enable_script_io(p) == {"AllowIoOsAccess": (None, True)}


def test_refuses_unexpected_structure(tmp_path):
    p = tmp_path / "settings.json"
    write(p, {"Video": {}})
    with pytest.raises(ValueError, match="Debug.ScriptWindow"):
        mesen_setup.enable_script_io(p)
    assert not (tmp_path / "settings.json.bak").exists()


def test_find_settings_explicit_and_portable(tmp_path):
    exe = tmp_path / "Mesen.exe"
    exe.write_bytes(b"x")
    assert mesen_setup.find_settings(tmp_path / "nao.json") is None
    (tmp_path / "settings.json").write_text("{}")
    assert mesen_setup.find_settings(mesen_exe=exe) == tmp_path / "settings.json"


def test_cli_setup_mesen(tmp_path, capsys):
    p = tmp_path / "s.json"
    write(p, {"Debug": {"ScriptWindow": {"AllowIoOsAccess": False}}})
    assert main(["setup-mesen", "--settings", str(p)]) == 0
    assert "AllowIoOsAccess" in capsys.readouterr().out
    assert main(["setup-mesen", "--settings", str(tmp_path / "x.json")]) == 1
