"""Calibra --gameplay-sprites a partir de uma sessão em que um humano jogou (modo `human`).

O modo human grava a sessão inteira (títulos, menus e gameplay). Informe em que segundo o gameplay
começou (`--gameplay-from`) e a ferramenta compara a contagem de sprites dos menus com a do jogo.
"""

import json
import math
from pathlib import Path

from packages.events.oam import visible_count

WARMUP_S = 5.0  # a OAM do boot tem lixo; o observador também ignora esse trecho


def _pct(values: list[int], p: float) -> int:
    v = sorted(values)
    return v[min(len(v) - 1, max(0, math.ceil(p * len(v)) - 1))]


def load_counts(path) -> list[tuple[float, int]]:
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if "oam" in row:
            out.append((row["f"] / 60.0, visible_count(row["oam"])))
    return out


def timeline(counts, step=5.0) -> list[dict]:
    rows = []
    t = 0.0
    end = counts[-1][0] if counts else 0
    while t <= end:
        block = [c for ts, c in counts if t <= ts < t + step]
        if block:
            rows.append(
                {"t": t, "min": min(block), "med": _pct(block, 0.5), "max": max(block)}
            )
        t += step
    return rows


def analyze(path, gameplay_from=None) -> dict:
    counts = load_counts(path)
    if len(counts) < 20:
        raise ValueError("sessão curta demais para calibrar (menos de 20 amostras)")
    res = {
        "samples": len(counts),
        "duration_s": counts[-1][0] - counts[0][0],
        "timeline": timeline(counts),
    }
    if gameplay_from is None:
        return res
    menu = [c for t, c in counts if WARMUP_S <= t < gameplay_from]
    game = [c for t, c in counts if t >= gameplay_from]
    if len(menu) < 10 or len(game) < 10:
        raise ValueError(
            "poucas amostras antes/depois de --gameplay-from (precisa de >= 10 de cada)"
        )
    m95, g05 = _pct(menu, 0.95), _pct(game, 0.05)
    res.update(menu_p95=m95, menu_max=max(menu), game_p5=g05, game_min=min(game))
    if m95 < g05:
        res["threshold"] = (m95 + g05 + 1) // 2 if (m95 + g05 + 1) // 2 > m95 else g05
        res["separable"] = True
    else:
        res["separable"] = False
    return res


def format_report(res: dict) -> str:
    lines = [
        f"{res['samples']} amostras, {res['duration_s']:.0f} s",
        "",
        "tempo   sprites (mín / mediana / máx)",
    ]
    for r in res["timeline"]:
        lines.append(f"{r['t']:5.0f}s  {r['min']:3d} / {r['med']:3d} / {r['max']:3d}")
    if "separable" not in res:
        lines += [
            "",
            "Veja acima em que segundo o gameplay começou e rode de novo com --gameplay-from SEGUNDOS.",
        ]
        return "\n".join(lines) + "\n"
    lines += [
        "",
        f"menus   (5 s .. início): 95% das amostras <= {res['menu_p95']} sprites (máx {res['menu_max']})",
        f"gameplay (depois)      : 95% das amostras >= {res['game_p5']} sprites (mín {res['game_min']})",
    ]
    if res["separable"]:
        lines.append(f"\nUse: --gameplay-sprites {res['threshold']}")
    else:
        lines += [
            "",
            "NÃO separável: menus e gameplay têm contagens de sprites sobrepostas neste jogo.",
            "Contar sprites não basta para distinguir menu de jogo aqui; é preciso outro detector.",
        ]
    return "\n".join(lines) + "\n"
