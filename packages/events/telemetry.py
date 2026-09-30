"""Carrega telemetria (JSONL). Dois formatos, detectados automaticamente (RFC 0002):

1) Telemetria direta (RAM/simulada): {"t","px","py","enemies":[...],"area"?,"event"?}
2) Trace OAM do observador (sem endereços de RAM): 1ª linha {"meta":{"source":"oam"}}
   + amostras {"f","in","oam","sc"?}
"""

import json
from pathlib import Path

from pydantic import ValidationError

from packages.schema.events import Frame, OamSample

from . import oam


def _rows(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_with_meta(path: str | Path) -> tuple[list[dict], dict]:
    rows = _rows(path)
    meta = rows[0]["meta"] if rows and "meta" in rows[0] else {}
    try:
        if meta.get("source") == "oam" or any("oam" in r for r in rows[:3]):
            for r in rows:
                if "oam" in r:
                    OamSample.model_validate(r)
            frames, meta = oam.convert(rows)
        else:
            frames = [
                Frame.model_validate(r).model_dump(exclude_none=True)
                for r in rows
                if "t" in r
            ]
    except ValidationError as exc:
        raise ValueError(f"{path}: telemetria fora do contrato — {exc}") from exc
    if len(frames) < 20:
        raise ValueError(
            "telemetria curta demais (mínimo 20 amostras): "
            "o jogo chegou a rodar/mostrar sprites?"
        )
    return frames, meta


def load(path: str | Path) -> list[dict]:
    return load_with_meta(path)[0]
