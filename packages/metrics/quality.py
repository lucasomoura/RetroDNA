"""Controle de qualidade por sessão (backlog da análise de 02/10/2026).

Uma sessão ruim (jogador mal identificado, bot parado, sessão curta) contamina a média do
Genome sem aviso. Aqui cada sessão recebe um veredito explícito e os motivos. Os limites são
heurísticas iniciais, não valores calibrados: ajuste quando houver mais dados reais.
"""

import math
from itertools import pairwise

MIN_DURATION_S = 20.0  # abaixo disso a sessão é curta demais para ritmo e encontros
MIN_PLAYER_CONFIDENCE = 0.15  # só para trace OAM (identificação do jogador)
MIN_MOVING_FRACTION = 0.15  # fração do tempo em que o jogador se move
MOVING_PX_S = 2.0  # velocidade mínima para contar como "movendo"


def moving_fraction(frames: list[dict]) -> float:
    moving = total = 0
    for a, b in pairwise(frames):
        dt = b["t"] - a["t"]
        if dt <= 0:
            continue
        total += 1
        moving += math.hypot(b["px"] - a["px"], b["py"] - a["py"]) / dt > MOVING_PX_S
    return round(moving / total, 3) if total else 0.0


def assess(frames: list[dict], meta: dict, metrics: dict) -> dict:
    """Devolve {"accepted": bool, "reasons": [...], "warnings": [...], "indicators": {...}}."""
    reasons, warnings = [], []
    mf = moving_fraction(frames)
    conf = meta.get("player_confidence")
    if metrics["duration_s"] < MIN_DURATION_S:
        reasons.append(
            f"sessão curta ({metrics['duration_s']}s < {MIN_DURATION_S:.0f}s)"
        )
    if conf is not None and conf < MIN_PLAYER_CONFIDENCE:
        reasons.append(
            f"jogador identificado com baixa confiança ({conf} < {MIN_PLAYER_CONFIDENCE})"
        )
    if mf < MIN_MOVING_FRACTION:
        reasons.append(
            f"jogador quase parado ({mf * 100:.0f}% do tempo em movimento "
            f"< {MIN_MOVING_FRACTION * 100:.0f}%)"
        )
    if metrics["encounters"] == 0:
        warnings.append("nenhum encontro com inimigos: ritmo de combate não medido")
    if meta.get("source") == "oam" and not meta.get("camera", True):
        warnings.append(
            "câmera não detectada: posições podem estar na tela, não no mundo"
        )
    return {
        "accepted": not reasons,
        "reasons": reasons,
        "warnings": warnings,
        "indicators": {
            "duration_s": metrics["duration_s"],
            "player_confidence": conf,
            "moving_fraction": mf,
            "encounters": metrics["encounters"],
        },
    }
