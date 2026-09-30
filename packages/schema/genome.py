"""Design Genome v0.2 (RFC 0001).

Somente métricas abstratas: nenhum sprite, mapa, áudio, código ou nome do jogo original.
Cada campo tem proveniência (`provenance`): measured | inferred | hypothesis | unavailable.
"""

import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .validation import pacing_issues

VERSION = "0.2"
NORMALIZATION = {
    "enemies_active_max": 8,
    "objectives_per_min": 2.0,
    "rewards_per_min": 4.0,
    "area_diagonal_px": 300.0,
}
DEFAULT_RATES = {"objectives_per_min": 1.0, "rewards_per_min": 2.0}
PROVENANCE_KEYS = {
    "movement.player_speed_px_s": "measured",
    "gameplay.exploration": "measured",
    "gameplay.combat": "measured",
    "gameplay.objective_density": "measured",
    "gameplay.enemy_density": "measured",
    "gameplay.reward_frequency": "measured",
    "level_design.average_area_size": "inferred",
    "level_design.alternate_routes": "inferred",
    "level_design.chokepoints": "inferred",
    "level_design.open_area_frequency": "unavailable",
    "pacing.average_exploration_time_s": "measured",
    "pacing.average_combat_duration_s": "measured",
    "pacing.average_time_between_encounters_s": "measured",
    "tension.curve": "hypothesis",
    "enemies.archetypes": "inferred",
    "raw.enemies_active_mean": "measured",
    "raw.objectives_per_min": "measured",
    "raw.rewards_per_min": "measured",
    "raw.encounters": "measured",
}

Unit = Annotated[float, Field(ge=0, le=1)]
Provenance = Literal["measured", "inferred", "hypothesis", "unavailable"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(_Strict):
    game: str
    sessions: int = Field(ge=1)
    duration_s: float = Field(ge=0)


class Movement(_Strict):
    player_speed_px_s: float = Field(ge=0)


class Gameplay(_Strict):
    exploration: Unit
    combat: Unit
    objective_density: Unit | None
    enemy_density: Unit
    reward_frequency: Unit | None


class LevelDesign(_Strict):
    average_area_size: Unit | None
    alternate_routes: Unit | None
    chokepoints: Unit | None
    open_area_frequency: Unit | None


class Pacing(_Strict):
    average_exploration_time_s: float = Field(ge=0)
    average_combat_duration_s: float = Field(ge=0)
    average_time_between_encounters_s: float = Field(ge=0)


class Tension(_Strict):
    curve: list[Unit] = Field(min_length=2)


class Archetype(_Strict):
    name: str
    speed_ratio: float = Field(ge=0)
    share: Unit


class Enemies(_Strict):
    archetypes: list[Archetype] = Field(min_length=1)


class Raw(_Strict):
    enemies_active_mean: float = Field(ge=0)
    objectives_per_min: float | None = Field(ge=0)
    rewards_per_min: float | None = Field(ge=0)
    encounters: int = Field(ge=0)


class Genome(_Strict):
    genome_version: Literal["0.2"]
    source: Source
    movement: Movement
    gameplay: Gameplay
    level_design: LevelDesign
    pacing: Pacing
    tension: Tension
    enemies: Enemies
    raw: Raw
    normalization: dict[str, float]
    provenance: dict[str, Provenance]

    @model_validator(mode="after")
    def _consistency(self) -> "Genome":
        missing = [k for k in PROVENANCE_KEYS if k not in self.provenance]
        if missing:
            raise ValueError(f"sem proveniência para: {', '.join(missing)}")
        issues = pacing_issues(self.pacing.model_dump(), self.raw.encounters)
        if issues:
            raise ValueError("; ".join(issues))
        return self


def validate(g: dict) -> dict:
    """Valida um genoma (dict) e o devolve normalizado. Levanta ValueError se inválido."""
    return Genome.model_validate(g).model_dump()


def load(path: str | Path) -> dict:
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))


def save(g: dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(g, indent=2, ensure_ascii=False), encoding="utf-8")


def rate(g: dict, key: str) -> float:
    """Taxa por minuto; usa um padrão quando o dado é indisponível (eventos não observados)."""
    v = g["raw"].get(key)
    return DEFAULT_RATES[key] if v is None else v
