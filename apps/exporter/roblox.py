"""Fase 4: exporta o mapa para Roblox (JSON + scripts Luau + plugin importador)."""

import json
import shutil
from pathlib import Path

TPL = Path(__file__).parent / "templates"


def export(m, out):
    out = Path(out)
    (out / "scripts").mkdir(parents=True, exist_ok=True)
    (out / "plugin").mkdir(exist_ok=True)
    for name, data in (
        ("map.json", m),
        ("enemies.json", m["enemies"]),
        ("items.json", m["items"]),
    ):
        (out / name).write_text(
            json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8"
        )
    for s in ("enemy.lua", "weapon.lua", "rescue.lua"):
        shutil.copy(TPL / s, out / "scripts" / s)
    shutil.copy(TPL / "RetroDNAImporter.lua", out / "plugin" / "RetroDNAImporter.lua")
    (out / "LEIAME.txt").write_text(
        "1) Salve plugin/RetroDNAImporter.lua como plugin local no Roblox Studio (Plugins > Plugins Folder).\n"
        "2) Clique em RetroDNA > Importar e escolha map.json.\n"
        "3) Cole os 3 scripts de scripts/ em ServerScriptService (tipo Script).\n",
        encoding="utf-8",
    )
