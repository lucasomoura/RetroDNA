"""Fase 2: DNA Analyzer. Separa DADO (medido), INTERPRETAÇÃO (regras sobre os dados) e HIPÓTESE."""

import json

NAMES = {
    "slow_chaser": "perseguidor lento",
    "steady_pursuer": "perseguidor constante",
    "fast_ambush": "emboscador rápido",
}


def report(g):
    P, G, tc = g["pacing"], g["gameplay"], g["tension"]["curve"]
    n = len(tc)
    peak = max(range(n), key=lambda i: tc[i])
    low = min(range(n), key=lambda i: tc[i])
    L = [
        "# Relatório do Design Genome",
        "",
        f"Fonte: {g['source']['game']} — {g['source']['sessions']} sessão(ões), {g['source']['duration_s']}s.",
        "",
        "## DADO (medido)",
        "",
    ]
    for path, prov in g["provenance"].items():
        sec, key = path.split(".")
        if prov == "measured":
            L.append(f"- `{path}` = {g[sec][key]}")
    L += ["", "## INTERPRETAÇÃO (regras sobre os dados)", ""]
    L.append(
        f"- Ritmo: {G['exploration'] * 100:.0f}% exploração / {G['combat'] * 100:.0f}% combate."
    )
    ratio = P["average_combat_duration_s"] / max(0.1, P["average_exploration_time_s"])
    L.append(
        "- Combates "
        + (
            "curtos frente à exploração"
            if ratio < 0.5
            else "de duração comparável à exploração"
            if ratio < 1.2
            else "mais longos que a exploração"
        )
        + f" ({P['average_combat_duration_s']}s de combate vs {P['average_exploration_time_s']}s de exploração)."
    )
    L.append(
        f"- Pico de tensão em {peak / (n - 1) * 100:.0f}% da sessão ({tc[peak]}); ponto mais calmo em {low / (n - 1) * 100:.0f}% ({tc[low]})."
    )
    relief = sum(1 for i in range(1, n) if tc[i - 1] > 0 and tc[i] < tc[i - 1] * 0.75)
    L.append(
        f"- {relief} queda(s) de tensão >25% entre segmentos (momentos de alívio)."
        if relief
        else "- Sem quedas de tensão marcantes (ritmo contínuo)."
    )
    trend = tc[-1] - tc[0]
    L.append(
        "- Progressão: tensão "
        + ("crescente" if trend > 0.1 else "decrescente" if trend < -0.1 else "estável")
        + "."
    )
    if g["raw"]["objectives_per_min"]:
        L.append(f"- Um objetivo a cada ~{60 / g['raw']['objectives_per_min']:.0f}s.")
    for a in g["enemies"]["archetypes"]:
        L.append(
            f"- {NAMES.get(a['name'], a['name'])}: {a['share'] * 100:.0f}% dos inimigos, {a['speed_ratio']}x a velocidade do jogador."
        )
    L += [
        "",
        "## HIPÓTESE (não verificado)",
        "",
        "- A curva de tensão usa uma fórmula experimental (v0); seus valores ainda não foram calibrados.",
        "- Métricas de level design (`inferred`) cobrem só as áreas visitadas na(s) sessão(ões).",
        f"- Com {g['source']['sessions']} sessão(ões), parte do ritmo reflete o comportamento do jogador, não só o design.",
    ]
    if g["source"]["sessions"] < 3:
        L.append(
            "- Recomenda-se agregar ao menos 3 sessões antes de confiar no Genome."
        )
    if g["provenance"].get("raw.rewards_per_min") == "unavailable":
        L.append(
            "- Eventos (dano, itens, objetivos) não foram observados: risco/recompensa da tensão valem 0 e o gerador usa taxas padrão."
        )
    miss = [k for k, v in g["provenance"].items() if v == "unavailable"]
    if miss:
        L.append("- Sem dados para: " + ", ".join(f"`{k}`" for k in miss) + ".")
    return "\n".join(L) + "\n"


def llm_prompt(g):
    return (
        "Você é analista de game design. Abaixo há um Design Genome com métricas e a proveniência de cada campo.\n"
        "Responda em três seções: DADO (repita só o que está como 'measured'), INTERPRETAÇÃO, HIPÓTESE.\n"
        "NÃO invente números; use apenas os do JSON. NÃO cite mapas, nomes ou assets do jogo original.\n\n```json\n"
        + json.dumps(g, indent=2, ensure_ascii=False)
        + "\n```\n"
    )
