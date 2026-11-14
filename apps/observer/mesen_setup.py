"""Configura o Mesen para o observador: liga 'Allow access to I/O and OS functions'.

A opção fica na janela "Debugger Settings" > aba "Script Window" > "Restrictions" e é gravada no
`settings.json` do Mesen. Este módulo edita só esse arquivo (com backup) e só se a estrutura
esperada existir (Debug.ScriptWindow); não cria nada às cegas.
"""

import json
import os
import shutil
import sys
from pathlib import Path

NAMES = ("MesenCE", "Mesen2", "Mesen")


class SettingsError(ValueError):
    """settings.json sem a estrutura esperada."""


WANTED = {"AllowIoOsAccess": True, "AutoStartScriptOnLoad": True}


def candidates(mesen_exe=None) -> list[Path]:
    paths: list[Path] = []
    if mesen_exe:
        paths.append(Path(mesen_exe).parent / "settings.json")  # modo portátil
    home = Path.home()
    if sys.platform.startswith("win"):
        bases = [home / "Documents"]
        bases += [
            Path(p)
            for p in (os.environ.get("APPDATA"), os.environ.get("LOCALAPPDATA"))
            if p
        ]
    elif sys.platform == "darwin":
        bases = [home / "Library" / "Application Support", home / "Documents"]
    else:
        bases = [home / ".config", home / ".local" / "share", home / "Documents"]
    paths += [b / n / "settings.json" for b in bases for n in NAMES]
    return paths


def find_settings(explicit=None, mesen_exe=None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.is_file() else None
    return next((p for p in candidates(mesen_exe) if p.is_file()), None)


def _key(d: dict, name: str) -> str | None:
    return next((k for k in d if k.lower() == name.lower()), None)


def enable_script_io(path) -> dict:
    """Liga as opções em WANTED. Devolve {chave: (antes, depois)} do que mudou."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    debug = data.get(_key(data, "Debug") or "", None)
    node = (
        debug.get(_key(debug, "ScriptWindow") or "", None)
        if isinstance(debug, dict)
        else None
    )
    if not isinstance(node, dict):
        raise SettingsError(
            f"{path} não tem Debug.ScriptWindow. Abra o Mesen, feche-o normalmente e tente de novo."
        )
    changes = {}
    for name, value in WANTED.items():
        k = _key(node, name)
        if k is None and name != "AllowIoOsAccess":
            continue  # só cria a chave principal; as demais só se já existirem
        before = node.get(k) if k else None
        if before != value:
            node[k or name] = value
            changes[name] = (before, value)
    if changes:
        shutil.copy2(path, path.with_name(path.name + ".bak"))
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return changes
