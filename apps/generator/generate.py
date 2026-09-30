"""Fase 3: gerador procedural guiado pelo Genome v0.2. Cria tudo do zero (nada do jogo original)."""

import random
from collections import deque

from packages.schema.genome import rate

W, H = 18, 22
DIRS = {"N": (0, -1), "S": (0, 1), "W": (-1, 0), "E": (1, 0)}
THEMES = {
    "humor": {
        "floor": "#8fd18f",
        "wall": "#6b4c9a",
        "names": {
            "slow_chaser": "Zumbi Bobo",
            "steady_pursuer": "Zumbi Atleta",
            "fast_ambush": "Zumbi Surpresa",
        },
        "npc": "Vizinho Assustado",
    },
    "terror": {
        "floor": "#2b2b2b",
        "wall": "#4a0d0d",
        "names": {
            "slow_chaser": "Sombra Arrastada",
            "steady_pursuer": "Vulto",
            "fast_ambush": "Espreitador",
        },
        "npc": "Sobrevivente",
    },
    "scifi": {
        "floor": "#1c2b4a",
        "wall": "#00c8ff",
        "names": {
            "slow_chaser": "Drone Lento",
            "steady_pursuer": "Sentinela",
            "fast_ambush": "Caçador Ciber",
        },
        "npc": "Tripulante",
    },
}
AGGRO = {"slow_chaser": 70, "steady_pursuer": 55, "fast_ambush": 35}
PATH_SAFETY = (
    0.6  # rota principal recebe 60% dos inimigos previstos (caminho mais seguro)
)


def _tension(tc, f):
    f = min(max(f, 0), 1) * (len(tc) - 1)
    i = int(f)
    j = min(i + 1, len(tc) - 1)
    return tc[i] + (tc[j] - tc[i]) * (f - i)


def _room_tiles(cell, adj, rnd):
    g = [
        ["#" if x in (0, W - 1) or y in (0, H - 1) else "." for x in range(W)]
        for y in range(H)
    ]
    for name, d in DIRS.items():
        if (cell[0] + d[0], cell[1] + d[1]) in adj[cell]:
            for k in (-1, 0, 1):
                if name == "N":
                    g[0][W // 2 + k] = "."
                if name == "S":
                    g[H - 1][W // 2 + k] = "."
                if name == "W":
                    g[H // 2 + k][0] = "."
                if name == "E":
                    g[H // 2 + k][W - 1] = "."
    for _ in range(rnd.randint(2, 4)):
        x, y = rnd.randint(3, W - 5), rnd.randint(3, H - 5)
        if abs(x - W // 2) < 3 or abs(y - H // 2) < 3:
            continue
        for dy in (0, 1):
            for dx in (0, 1):
                g[y + dy][x + dx] = "#"
    return ["".join(r) for r in g]


def generate(genome, theme="humor", seed=1, minutes=8, seconds_per_room=None):
    rnd = random.Random(seed)
    th = THEMES[theme]
    # HIPÓTESE: uma sala ~ um encontro; logo segundos por sala = intervalo médio entre encontros.
    spr = seconds_per_room or max(
        15.0, genome["pacing"]["average_time_between_encounters_s"]
    )
    n = max(4, round(minutes * 60 / spr))
    alt = genome["level_design"]["alternate_routes"]
    alt = 0.12 if alt is None else alt

    order, cells, edges = [(0, 0)], {(0, 0)}, set()
    while len(cells) < n:
        c = rnd.choice(order)
        d = rnd.choice(list(DIRS.values()))
        nb = (c[0] + d[0], c[1] + d[1])
        if nb in cells:
            continue
        cells.add(nb)
        order.append(nb)
        edges.add(frozenset((c, nb)))
    cand = sorted(
        (c, (c[0] + d[0], c[1] + d[1]))
        for c in cells
        for d in ((1, 0), (0, 1))
        if (c[0] + d[0], c[1] + d[1]) in cells
        and frozenset((c, (c[0] + d[0], c[1] + d[1]))) not in edges
    )
    rnd.shuffle(cand)
    for a, b in cand[
        : round(alt * n)
    ]:  # rotas alternativas = laços extras (complexidade ciclomática / salas)
        edges.add(frozenset((a, b)))
    adj = {c: set() for c in cells}
    for e in edges:
        a, b = tuple(e)
        adj[a].add(b)
        adj[b].add(a)

    start = order[0]
    depth, parent, q = {start: 0}, {}, deque([start])
    while q:
        c = q.popleft()
        for nb in sorted(adj[c]):
            if nb not in depth:
                depth[nb] = depth[c] + 1
                parent[nb] = c
                q.append(nb)
    exit_cell = max(sorted(depth), key=depth.get)
    path, c = [exit_cell], exit_cell
    while c != start:
        c = parent[c]
        path.append(c)
    path.reverse()
    maxd = max(depth.values()) or 1

    minx = min(c[0] for c in cells)
    miny = min(c[1] for c in cells)
    ids = {c: f"r{i}" for i, c in enumerate(sorted(cells))}
    tc = genome["tension"]["curve"]
    arch = genome["enemies"]["archetypes"]
    weights = [a["share"] for a in arch]

    tens, base = {}, {}
    for c in sorted(cells):
        on_path = c in path
        f = path.index(c) / max(1, len(path) - 1) if on_path else depth[c] / maxd
        tens[c] = _tension(tc, f)
        base[c] = 0.0 if c == start else tens[c] * (PATH_SAFETY if on_path else 1.0)
    total_target = (
        genome["raw"]["enemies_active_mean"] * n
    )  # preserva a densidade média medida
    s = sum(base.values())
    k = total_target / s if s > 0 else 0

    rooms, enemies = [], []
    for c in sorted(cells):
        ox, oy = (c[0] - minx) * W, (c[1] - miny) * H
        tiles = _room_tiles(c, adj, rnd)
        floor = [
            (x, y)
            for y in range(2, H - 2)
            for x in range(2, W - 2)
            if tiles[y][x] == "."
        ]
        for _ in range(min(12, round(base[c] * k))):
            a = rnd.choices(arch, weights)[0]
            x, y = rnd.choice(floor)
            enemies.append(
                {
                    "room": ids[c],
                    "archetype": a["name"],
                    "type": th["names"].get(a["name"], a["name"]),
                    "speed": round(16 * a["speed_ratio"], 1),
                    "aggro": AGGRO.get(a["name"], 50),
                    "health": 30,
                    "x": ox + x,
                    "y": oy + y,
                }
            )
        rooms.append(
            {
                "id": ids[c],
                "cell": list(c),
                "origin": [ox, oy],
                "on_main_path": c in path,
                "tension": round(tens[c], 3),
                "connections": sorted(ids[nb] for nb in adj[c]),
                "tiles": tiles,
            }
        )

    def spot(r):
        x, y = rnd.choice(
            [
                (x, y)
                for y in range(2, H - 2)
                for x in range(2, W - 2)
                if r["tiles"][y][x] == "."
            ]
        )
        return r["origin"][0] + x, r["origin"][1] + y

    non_start = [r for r in rooms if r["id"] != ids[start]]
    want_items = round(
        rate(genome, "rewards_per_min") * minutes
    )  # recompensas nas salas mais calmas
    items = []
    for r in sorted(non_start, key=lambda r: (r["tension"], r["id"]))[:want_items]:
        x, y = spot(r)
        items.append({"room": r["id"], "kind": "ammo", "amount": 10, "x": x, "y": y})
    want_npcs = round(rate(genome, "objectives_per_min") * minutes)
    off = [r for r in non_start if not r["on_main_path"]] or non_start
    npcs = []
    for r in rnd.sample(off, min(want_npcs, len(off))):
        x, y = spot(r)
        npcs.append({"room": r["id"], "type": th["npc"], "x": x, "y": y})

    return {
        "format": "retrodna-map/1",
        "theme": theme,
        "seed": seed,
        "tile_size": 4,
        "room_size": [W, H],
        "params": {"minutes": minutes, "seconds_per_room": round(spr, 1)},
        "palette": {"floor": th["floor"], "wall": th["wall"]},
        "start_room": ids[start],
        "exit_room": ids[exit_cell],
        "main_path": [ids[c] for c in path],
        "rooms": rooms,
        "enemies": enemies,
        "npcs": npcs,
        "items": items,
        "stats": {
            "rooms": len(rooms),
            "enemies": len(enemies),
            "npcs": len(npcs),
            "items": len(items),
            "enemies_per_room": round(len(enemies) / len(rooms), 2),
        },
    }
