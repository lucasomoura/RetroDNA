"""Contratos de telemetria (RFC 0002): o que o Observer entrega ao resto do pipeline."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EventName = Literal["damage", "kill", "rescue", "item"]
OAM_HEX_LEN = 544 * 2  # OAM do SNES: 512 B (128 sprites) + 32 B de bits altos


class Entity(BaseModel):
    id: int
    x: float
    y: float
    type: int | None = None


class Frame(BaseModel):
    """Amostra de telemetria direta (~10 Hz)."""

    t: float
    px: float
    py: float
    enemies: list[Entity] = Field(default_factory=list)
    area: str | None = None
    event: EventName | None = None


class OamSample(BaseModel):
    """Amostra bruta do observador OAM (sem endereços de RAM)."""

    model_config = ConfigDict(populate_by_name=True)

    f: int = Field(ge=0)
    inputs: str = Field(default="", alias="in")
    oam: str = Field(min_length=OAM_HEX_LEN, max_length=OAM_HEX_LEN)
    sc: dict[str, float] | None = None
