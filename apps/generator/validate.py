"""Fase 9: valida se o mapa gerado respeita o Genome. Mede o mapa e compara com o alvo.
level 'error' reprova o pipeline; 'warn' apenas alerta."""

import statistics

from packages.schema.genome import rate
from packages.utils.stats import pearson


def _reach(ids, adj, start, banned=None):
    seen, st = {start}, [start]
    while st:
        for nb in adj[st.pop()]:
            if nb != banned and nb not in seen:
                seen.add(nb)
                st.append(nb)
    return seen


def validate_map(m, g):
    rooms = {r["id"]: r for r in m["rooms"]}
    adj = {i: set(r["connections"]) for i, r in rooms.items()}
    V = len(rooms)
    E = sum(len(s) for s in adj.values()) // 2
    minutes = m["params"]["minutes"]
    checks = []

    def add(name, expected, actual, ok, level="error", note=""):
        checks.append(
            {
                "check": name,
                "expected": expected,
                "actual": actual,
                "ok": bool(ok),
                "level": level,
                "note": note,
            }
        )

    reach = _reach(rooms, adj, m["start_room"])
    add(
        "conectividade",
        "todas as salas alcançáveis",
        f"{len(reach)}/{V}",
        len(reach) == V and m["exit_room"] in reach,
    )

    bad = 0
    for kind in ("enemies", "npcs", "items"):
        for e in m[kind]:
            r = rooms[e["room"]]
            lx, ly = e["x"] - r["origin"][0], e["y"] - r["origin"][1]
            bad += not (
                0 <= ly < len(r["tiles"])
                and 0 <= lx < len(r["tiles"][0])
                and r["tiles"][ly][lx] == "."
            )
    add("entidades em piso livre", "0 fora do piso", bad, bad == 0)

    est = V * m["params"]["seconds_per_room"] / 60
    add(
        "duração estimada (min)",
        minutes,
        round(est, 2),
        abs(est - minutes) <= 0.15 * minutes,
        "warn",
        "HIPÓTESE: 1 sala ≈ 1 encontro",
    )

    target = g["raw"]["enemies_active_mean"]
    epr = len(m["enemies"]) / V
    add(
        "densidade de inimigos/sala",
        target,
        round(epr, 2),
        abs(epr - target) <= 0.4 * max(target, 0.1),
        note="tol ±40%",
    )

    counts = {i: 0 for i in rooms}
    for e in m["enemies"]:
        counts[e["room"]] += 1
    ns = [i for i in rooms if i != m["start_room"]]
    r = pearson([rooms[i]["tension"] for i in ns], [counts[i] for i in ns])
    add(
        "tensão guia inimigos (r)",
        ">= 0.6",
        None if r is None else round(r, 2),
        r is not None and r >= 0.6,
    )

    path = m["main_path"]
    K = len(g["tension"]["curve"])
    prof = [counts[path[round(i * (len(path) - 1) / (K - 1))]] for i in range(K)]
    r2 = pearson(prof, g["tension"]["curve"])
    add(
        "perfil na rota vs curva (r)",
        ">= 0.4",
        None if r2 is None else round(r2, 2),
        r2 is not None and r2 >= 0.4,
        "warn",
    )

    on = [counts[i] for i in path if i != m["start_room"]]
    off = [counts[i] for i in rooms if i not in path]
    if on and off:
        a, b = statistics.mean(on), statistics.mean(off)
        add(
            "rota principal mais segura",
            "média rota <= média fora",
            f"{a:.2f} vs {b:.2f}",
            a <= b,
        )

    want_n = round(rate(g, "objectives_per_min") * minutes)
    add(
        "objetivos (NPCs)",
        want_n,
        len(m["npcs"]),
        abs(len(m["npcs"]) - want_n) <= 1,
        note="tol ±1",
    )
    want_i = round(rate(g, "rewards_per_min") * minutes)
    add(
        "recompensas (itens)",
        want_i,
        len(m["items"]),
        abs(len(m["items"]) - want_i) <= 1,
        note="tol ±1",
    )

    alt_t = g["level_design"]["alternate_routes"]
    if alt_t is not None:
        alt = max(0, E - V + 1) / V
        add(
            "rotas alternativas",
            alt_t,
            round(alt, 3),
            abs(alt - alt_t) <= 0.15,
            note="tol ±0.15",
        )
    ch_t = g["level_design"]["chokepoints"]
    if ch_t is not None and V >= 3:
        ch = (
            sum(
                1
                for i in rooms
                if len(_reach(rooms, adj, next(j for j in rooms if j != i), banned=i))
                < V - 1
            )
            / V
        )
        add(
            "gargalos (fração)",
            ch_t,
            round(ch, 3),
            abs(ch - ch_t) <= 0.25,
            "warn",
            "tol ±0.25; gerador não controla",
        )

    errors = [c for c in checks if not c["ok"] and c["level"] == "error"]
    return {
        "passed": not errors,
        "errors": len(errors),
        "warnings": sum(1 for c in checks if not c["ok"] and c["level"] == "warn"),
        "checks": checks,
    }


def to_markdown(v):
    L = [
        "# Validação do mapa vs Genome",
        "",
        (
            f"Resultado: {'APROVADO' if v['passed'] else 'REPROVADO'} "
            f"({v['errors']} erro(s), {v['warnings']} aviso(s))"
        ),
        "",
        "| Check | Esperado | Obtido | Status |",
        "|---|---|---|---|",
    ]
    for c in v["checks"]:
        st = "ok" if c["ok"] else ("FALHA" if c["level"] == "error" else "aviso")
        L.append(f"| {c['check']} | {c['expected']} | {c['actual']} | {st} |")
    return "\n".join(L) + "\n"
