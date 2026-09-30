"""Gera telemetria sintética para testar o pipeline sem emulador."""

import json
import math
import random


def make(path, minutes=6, hz=10, seed=7):
    rnd = random.Random(seed)
    px = py = ang = 0.0
    speed = 48.0
    enemies = {}
    nid = 0
    total = int(minutes * 60 * hz)
    next_rescue, next_item = 50.0, 25.0
    with open(path, "w", encoding="utf-8") as f:
        for i in range(total):
            t = i / hz
            phase = t / (minutes * 60)
            wave = (0.5 + 0.5 * math.sin(phase * 2 * math.pi * 2.2 - 1.2)) * (
                0.4 + 0.8 * phase
            )
            if rnd.random() < 0.02:
                ang += rnd.uniform(-1.5, 1.5)
            px += math.cos(ang) * speed / hz
            py += math.sin(ang) * speed / hz
            if len(enemies) < 8 and rnd.random() < 0.05 * wave:
                nid += 1
                a = rnd.uniform(0, 6.283)
                r = rnd.uniform(90, 160)
                k = rnd.choices([0.5, 0.9, 1.4], [60, 15, 25])[0]
                enemies[nid] = [px + math.cos(a) * r, py + math.sin(a) * r, speed * k]
            event = None
            for eid in list(enemies):
                ex, ey, es = enemies[eid]
                d = math.hypot(px - ex, py - ey) or 1
                enemies[eid][0] += (px - ex) / d * es / hz
                enemies[eid][1] += (py - ey) / d * es / hz
                if d < 12:
                    event = "damage"
                    del enemies[eid]
                elif d < 40 and rnd.random() < 0.05:
                    event = "kill"
                    del enemies[eid]
                elif d > 300:
                    del enemies[eid]
            if t >= next_rescue and event is None:
                event = "rescue"
                next_rescue += rnd.uniform(45, 70)
            if t >= next_item and event is None:
                event = "item"
                next_item += rnd.uniform(18, 35)
            fr = {
                "t": round(t, 2),
                "px": round(px, 1),
                "py": round(py, 1),
                "area": f"{int(px // 300)}_{int(py // 300)}",
                "enemies": [
                    {"id": k, "x": round(v[0], 1), "y": round(v[1], 1)}
                    for k, v in enemies.items()
                ],
            }
            if event:
                fr["event"] = event
            f.write(json.dumps(fr) + "\n")
