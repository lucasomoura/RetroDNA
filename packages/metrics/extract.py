"""Fase 1: telemetria -> métricas medidas (sem IA, sem inventar números).
Telemetria opcional: campo "area" por amostra (habilita métricas de level design) e eventos
"damage" | "kill" | "rescue" (objetivo) | "item" (recompensa)."""

import math
import statistics
from itertools import pairwise

NEAR = 64.0  # px: distância que conta como "em combate"
GAP = 3.0  # s: pausa que separa dois encontros
SEGMENTS = 8  # pontos da curva de tensão
AREA_REF = 300.0  # px: diagonal de referência para average_area_size (=1.0)
# Tensão v0 (experimental): + inimigos + proximidade + risco + duração - recompensa - segurança
W_N, W_PROX, W_RISK, W_DUR = 0.35, 0.25, 0.20, 0.20
REWARD_RELIEF, SAFE_RELIEF = 0.15, 0.10

SCALARS = [
    "duration_s",
    "player_speed",
    "enemies_active_mean",
    "combat_ratio",
    "combat_duration_s",
    "exploration_time_s",
    "encounter_interval_s",
    "encounters",
    "objectives_per_min",
    "rewards_per_min",
    "average_area_size",
    "alternate_routes",
    "chokepoints",
]


def _articulation_fraction(nodes, adj):
    if len(nodes) < 3:
        return 0.0
    cnt = 0
    for r in nodes:
        rest = [n for n in nodes if n != r]
        seen, st = {rest[0]}, [rest[0]]
        while st:
            for nb in adj[st.pop()]:
                if nb != r and nb not in seen:
                    seen.add(nb)
                    st.append(nb)
        cnt += len(seen) < len(rest)
    return cnt / len(nodes)


def _level_design(frames):
    if not any("area" in f for f in frames):
        return None, None, None
    boxes, adj, last = {}, {}, None
    for f in frames:
        a = f.get("area")
        if a is None:
            continue
        b = boxes.setdefault(a, [f["px"], f["py"], f["px"], f["py"]])
        b[0], b[1] = min(b[0], f["px"]), min(b[1], f["py"])
        b[2], b[3] = max(b[2], f["px"]), max(b[3], f["py"])
        adj.setdefault(a, set())
        if last is not None and last != a:
            adj[last].add(a)
            adj[a].add(last)
        last = a
    V = len(adj)
    E = sum(len(s) for s in adj.values()) // 2
    size = (
        statistics.mean(math.hypot(b[2] - b[0], b[3] - b[1]) for b in boxes.values())
        / AREA_REF
    )
    return (
        round(min(1.0, size), 3),
        round(min(1.0, max(0, E - V + 1) / V), 3),
        round(_articulation_fraction(list(adj), adj), 3),
    )


def extract(frames, segments=SEGMENTS, meta=None):
    events_ok = (meta or {}).get("events", True)
    dur = frames[-1]["t"] - frames[0]["t"]
    psp, esp = [], {}
    for a, b in pairwise(frames):
        dt = b["t"] - a["t"]
        if dt <= 0:
            continue
        d = math.hypot(b["px"] - a["px"], b["py"] - a["py"]) / dt
        if 0 < d < 1000:
            psp.append(d)
        prev = {e["id"]: e for e in a["enemies"]}
        for e in b["enemies"]:
            p = prev.get(e["id"])
            if p:
                v = math.hypot(e["x"] - p["x"], e["y"] - p["y"]) / dt
                if v < 1000:
                    esp.setdefault(e["id"], []).append(v)
    pspeed = statistics.median(psp) if psp else 0.0

    near_flags, tension, enc = [], [], []
    last_dmg = last_item = last_near = -99.0
    enc_start = None
    for fr in frames:
        t, ev = fr["t"], fr.get("event")
        last_dmg = t if ev == "damage" else last_dmg
        last_item = t if ev == "item" else last_item
        ds = [math.hypot(e["x"] - fr["px"], e["y"] - fr["py"]) for e in fr["enemies"]]
        n = sum(1 for d in ds if d < NEAR)
        near_flags.append(n > 0)
        if n > 0:
            if enc_start is None or t - last_near > GAP:
                if enc_start is not None:
                    enc.append((enc_start, last_near))
                enc_start = t
            last_near = t
        nearest = min(ds) if ds else None
        prox = max(0.0, 1 - nearest / (2 * NEAR)) if ds else 0.0
        risk = 1.0 if t - last_dmg < 2 else 0.0
        durf = (
            min(1.0, (t - enc_start) / 20) if (n > 0 and enc_start is not None) else 0.0
        )
        v = W_N * min(1.0, n / 3) + W_PROX * prox + W_RISK * risk + W_DUR * durf
        if t - last_item < 5:
            v -= REWARD_RELIEF
        if not ds or nearest >= 2 * NEAR:
            v -= SAFE_RELIEF
        tension.append(min(1.0, max(0.0, v)))
    if enc_start is not None:
        enc.append((enc_start, last_near))

    seg = max(1, len(tension) // segments)
    curve = [
        round(
            sum(tension[i * seg : (i + 1) * seg])
            / len(tension[i * seg : (i + 1) * seg]),
            3,
        )
        for i in range(segments)
    ]

    groups = {"slow_chaser": [], "steady_pursuer": [], "fast_ambush": []}
    for v in esp.values():
        if pspeed and v:
            r = statistics.median(v) / pspeed
            groups[
                "slow_chaser"
                if r < 0.75
                else "steady_pursuer"
                if r < 1.1
                else "fast_ambush"
            ].append(r)
    total = sum(len(g) for g in groups.values()) or 1
    archetypes = [
        {
            "name": k,
            "speed_ratio": round(sum(g) / len(g), 2),
            "share": round(len(g) / total, 2),
        }
        for k, g in groups.items()
        if g
    ]

    durs = [e - s for s, e in enc]
    gaps = [enc[i + 1][0] - enc[i][1] for i in range(len(enc) - 1)]
    ints = [enc[i + 1][0] - enc[i][0] for i in range(len(enc) - 1)]
    mins = dur / 60 if dur else 1
    count = lambda name: sum(1 for f in frames if f.get("event") == name)
    size, alt, choke = _level_design(frames)
    m = {
        "duration_s": round(dur, 1),
        "player_speed": round(pspeed, 2),
        "enemies_active_mean": round(
            sum(len(f["enemies"]) for f in frames) / len(frames), 2
        ),
        "combat_ratio": round(sum(near_flags) / len(near_flags), 3),
        "combat_duration_s": round(statistics.mean(durs), 1) if durs else 0.0,
        "exploration_time_s": round(statistics.mean(gaps), 1)
        if gaps
        else round(dur, 1),
        "encounter_interval_s": round(statistics.mean(ints), 1)
        if ints
        else round(dur, 1),
        "encounters": len(enc),
        "objectives_per_min": round(count("rescue") / mins, 2) if events_ok else None,
        "rewards_per_min": round(count("item") / mins, 2) if events_ok else None,
        "average_area_size": size,
        "alternate_routes": alt,
        "chokepoints": choke,
        "tension_curve": curve,
        "enemy_archetypes": archetypes,
        "sessions": 1,
    }
    return m


def aggregate(ms):
    """Agrega várias sessões (média). Reduz o viés de uma única partida."""
    if len(ms) == 1:
        return ms[0]
    out = {}
    for k in SCALARS:
        vals = [m[k] for m in ms if m.get(k) is not None]
        out[k] = round(statistics.mean(vals), 3) if vals else None
    out["duration_s"] = round(sum(m["duration_s"] for m in ms), 1)
    out["encounters"] = int(sum(m["encounters"] for m in ms))
    out["tension_curve"] = [
        round(statistics.mean(m["tension_curve"][i] for m in ms), 3)
        for i in range(len(ms[0]["tension_curve"]))
    ]
    by = {}
    for m in ms:
        for a in m["enemy_archetypes"]:
            by.setdefault(a["name"], []).append(a)
    tot = sum(statistics.mean(x["share"] for x in v) for v in by.values()) or 1
    out["enemy_archetypes"] = [
        {
            "name": k,
            "speed_ratio": round(statistics.mean(x["speed_ratio"] for x in v), 2),
            "share": round(statistics.mean(x["share"] for x in v) / tot, 2),
        }
        for k, v in by.items()
    ]
    out["sessions"] = len(ms)
    return out
