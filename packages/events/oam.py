"""Converte trace de OAM (sprites) em telemetria: identifica o jogador pela correlação com o input
e rastreia os demais objetos móveis como inimigos. Funciona sem endereços de RAM de nenhum jogo."""

import math
from itertools import pairwise

from packages.utils.stats import pearson

LINK = 20  # px: sprites a esta distância formam um objeto
MATCH = 36  # px: distância máxima para ligar um objeto entre amostras
MIN_TRACK = 15  # amostras mínimas para candidato a jogador
MIN_ENEMY_LEN = 8
MIN_MOVE = 8.0  # px de deslocamento total para não ser cenário


def parse(hexstr):
    b = bytes.fromhex(hexstr)
    out = []
    for i in range(128):
        x, y, tile = b[4 * i], b[4 * i + 1], b[4 * i + 2]
        hi = b[512 + i // 4] >> ((i % 4) * 2)
        X = x - 256 if hi & 1 else x
        size = 16 if hi & 2 else 8
        if y < 224 and -size < X < 256:
            out.append((i, X + size / 2, y + size / 2, tile))
    return out


def _corr(a, b):
    r = pearson(a, b) if len(a) >= 5 else None
    return 0.0 if r is None else r


def _camera(samples):
    """Escolhe a camada de scroll que mais varia e devolve (cx, cy) acumulados por amostra, ou None."""
    keys = {k for s in samples for k in (s.get("sc") or {})}

    def spread(k):
        v = [s["sc"][k] for s in samples if s.get("sc") and k in s["sc"]]
        return (max(v) - min(v)) if v else 0

    def pick(prefix):
        c = [k for k in keys if k.lower().split(".")[-1].startswith(prefix)]
        return max(c, key=spread) if c and max(spread(k) for k in c) > 0 else None

    hk, vk = pick("h"), pick("v")
    if not hk and not vk:
        return None

    def unwrap(k):
        out, cum, prev = [], 0, None
        for s in samples:
            v = (s.get("sc") or {}).get(k, prev or 0)
            if prev is not None:
                d = v - prev
                d = d - 1024 if d > 512 else d + 1024 if d < -512 else d
                cum += d
            prev = v
            out.append(cum)
        return out

    cx = unwrap(hk) if hk else [0] * len(samples)
    cy = unwrap(vk) if vk else [0] * len(samples)
    return list(zip(cx, cy))


def _clusters(pts):
    parent = list(range(len(pts)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if max(abs(pts[i][1] - pts[j][1]), abs(pts[i][2] - pts[j][2])) <= LINK:
                parent[find(i)] = find(j)
    groups = {}
    for i, p in enumerate(pts):
        groups.setdefault(find(i), []).append(p)
    return [
        (
            sum(p[1] for p in g) / len(g),
            sum(p[2] for p in g) / len(g),
            tuple(sorted(p[3] for p in g)),
        )
        for g in groups.values()
    ]


def _track(per, cam, static):
    tracks, active, nid = {}, {}, 0
    for k, pts in enumerate(per):
        cx, cy = cam[k] if cam else (0, 0)
        ents = [
            (x + cx, y + cy, sig)
            for x, y, sig in _clusters([p for p in pts if p[0] not in static])
        ]
        pairs = sorted(
            (math.hypot(tr["last"][0] - e[0], tr["last"][1] - e[1]), tid, j)
            for tid, tr in active.items()
            for j, e in enumerate(ents)
        )
        used_t, used_e = set(), set()
        for d, tid, j in pairs:
            if d <= MATCH and tid not in used_t and j not in used_e:
                used_t.add(tid)
                used_e.add(j)
                tracks[tid]["pts"].append((k, *ents[j]))
                active[tid]["last"] = ents[j]
                active[tid]["seen"] = k
        for j, e in enumerate(ents):
            if j not in used_e:
                nid += 1
                tracks[nid] = {"pts": [(k, *e)]}
                active[nid] = {"last": e, "seen": k}
        for tid in [t for t, a in active.items() if k - a["seen"] > 3]:
            del active[tid]
    return tracks


def _pick_player(tracks, ix, iy):
    act = [1 if (a or b) else 0 for a, b in zip(ix, iy)]

    def score(tr):
        p = tr["pts"]
        dx, dy, sx, sy, an, ac = [], [], [], [], [], []
        for a, b in pairwise(p):
            if b[0] - a[0] == 1:
                dx.append(b[1] - a[1])
                dy.append(b[2] - a[2])
                sx.append(ix[b[0]])
                sy.append(iy[b[0]])
                an.append(1 if a[3] != b[3] else 0)
                ac.append(act[b[0]])
        # movimento no mundo correlacionado ao input + animação (troca de tiles) correlacionada ao input
        return abs(_corr(dx, sx)) + abs(_corr(dy, sy)) + 2 * abs(_corr(an, ac))

    cand = {t: tr for t, tr in tracks.items() if len(tr["pts"]) >= MIN_TRACK}
    if not cand:
        return None, 0.0
    sc = {t: score(tr) for t, tr in cand.items()}
    best = max(
        cand, key=lambda t: sc[t] * math.sqrt(len(cand[t]["pts"]))
    )  # rastros curtos não vencem por acaso
    conf = sc[best] / 2  # 0..~2: correlação de movimento + animação com o input
    return (
        best if conf >= 0.15 else max(cand, key=lambda t: len(cand[t]["pts"]))
    ), conf


def convert(rows):
    meta = dict(rows[0]["meta"]) if rows and "meta" in rows[0] else {}
    samples = [r for r in rows if "oam" in r]
    per = [parse(s["oam"]) for s in samples]
    seen = {}
    for pts in per:
        for i, x, y, t in pts:
            seen.setdefault(i, []).append((x, y, t))
    # HUD: índice OAM visível em >=50% das amostras, sem mover e sem trocar de tile
    static = {
        i
        for i, v in seen.items()
        if len(v) >= 0.5 * len(per)
        and max(p[0] for p in v) - min(p[0] for p in v) <= 1
        and max(p[1] for p in v) - min(p[1] for p in v) <= 1
        and len({p[2] for p in v}) == 1
    }
    cam = _camera(samples)
    ix, iy = [], []
    for s in samples:
        p = set((s.get("in") or "").split(","))
        ix.append(("right" in p) - ("left" in p))
        iy.append(("down" in p) - ("up" in p))

    tracks = _track(per, cam, static)
    player, conf = _pick_player(tracks, ix, iy)
    if (
        player is None and static
    ):  # jogador sem animação pode ter sido tomado por HUD: tenta sem o filtro
        tracks = _track(per, cam, set())
        player, conf = _pick_player(tracks, ix, iy)
    meta.update(
        {
            "source": "oam",
            "events": False,
            "area": False,
            "camera": cam is not None,
            "player_confidence": round(conf, 2),
            "tracks": len(tracks),
        }
    )
    if player is None:
        return [], meta

    def moved(tr):
        p = tr["pts"]
        return sum(math.hypot(b[1] - a[1], b[2] - a[2]) for a, b in pairwise(p))

    # o jogador pode fragmentar (inimigo encosta e "cola" o objeto): une rastros cujos tiles pertencem ao jogador
    ptiles = {t for _, _, _, sig in tracks[player]["pts"] for t in sig}
    mine = {player} | {
        t
        for t, tr in tracks.items()
        if t != player
        and len(tr["pts"]) >= 3
        and sum(1 for *_, sig in tr["pts"] if set(sig) <= ptiles)
        >= 0.8 * len(tr["pts"])
    }

    enemy_ids = {
        t
        for t, tr in tracks.items()
        if t not in mine and len(tr["pts"]) >= MIN_ENEMY_LEN and moved(tr) >= MIN_MOVE
    }
    at, pl = {}, {}
    for t in enemy_ids:
        for k, x, y, _ in tracks[t]["pts"]:
            at.setdefault(k, {})[t] = (x, y)
    for t in mine:
        for k, x, y, _ in tracks[t]["pts"]:
            pl.setdefault(k, []).append((x, y))
    frames, last = [], None
    for k, s in enumerate(samples):
        if k not in pl:
            continue
        px, py = (
            min(pl[k], key=lambda p: math.hypot(p[0] - last[0], p[1] - last[1]))
            if last
            else pl[k][0]
        )
        last = (px, py)
        frames.append(
            {
                "t": round(s["f"] / 60.0, 2),
                "px": round(px, 1),
                "py": round(py, 1),
                "enemies": [
                    {"id": t, "x": round(p[0], 1), "y": round(p[1], 1)}
                    for t, p in at.get(k, {}).items()
                ],
            }
        )
    return frames, meta
