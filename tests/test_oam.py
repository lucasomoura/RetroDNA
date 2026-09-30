import json
import math
import os
import random
import tempfile
import unittest

from apps.generator import generate, validate
from apps.observer import auto
from packages.events import oam, telemetry
from packages.metrics import build_genome, extract
from packages.schema import genome


def oam_hex(sprites):
    b = bytearray(544)
    for i in range(128):
        b[4 * i + 1] = 240
    for i, (x, y, t, l) in enumerate(sprites):
        b[4 * i], b[4 * i + 1], b[4 * i + 2] = x & 0xFF, y, t
        b[512 + i // 4] |= ((1 if x < 0 else 0) | (l << 1)) << ((i % 4) * 2)
    return b.hex()


def make_trace(path, seconds=240, seed=3, camera=True):
    """Câmera segue o jogador (jogador fixo na tela): só o scroll revela o movimento real."""
    rnd = random.Random(seed)
    px = py = 1000.0
    held, hold_until, enemies, nid = (0, 0), 0, {}, 0
    truth = []
    with open(path, "w") as f:
        f.write(
            json.dumps({"meta": {"source": "oam", "mode": "bot", "every": 6}}) + "\n"
        )
        for fr in range(1, seconds * 60 + 1):
            if fr >= hold_until:
                held = rnd.choice(
                    [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]
                )
                hold_until = fr + rnd.randint(20, 90)
            px += held[0] * 1.2
            py += held[1] * 1.2
            if len(enemies) < 5 and rnd.random() < 0.01:
                a = rnd.uniform(0, 6.28)
                enemies[nid] = [
                    px + math.cos(a) * 120,
                    py + math.sin(a) * 120,
                    rnd.choice([0.5, 1.4]),
                ]
                nid += 1
            for k in list(enemies):
                e = enemies[k]
                d = math.hypot(px - e[0], py - e[1]) or 1
                e[0] += (px - e[0]) / d * e[2]
                e[1] += (py - e[1]) / d * e[2]
                if d < 10 and rnd.random() < 0.3:
                    del enemies[k]
            if fr % 6:
                continue
            cx, cy = (px - 128) if camera else 0, (py - 112) if camera else 0
            spr = [
                (8, 8, 1, 0),
                (16, 8, 2 + (fr // 600) % 3, 0),
                (24, 8, 3, 0),
            ]  # HUD fixo (um dígito muda de vez em quando)
            sx, sy = (128, 112) if camera else (px % 256, py % 224)
            anim = 4 * ((fr // 12) % 2) if held != (0, 0) else 0
            spr += [
                (sx, sy, 10 + anim, 0),
                (sx + 8, sy, 11 + anim, 0),
                (sx, sy + 8, 12 + anim, 0),
                (sx + 8, sy + 8, 13 + anim, 0),
            ]  # jogador 2x2 animado
            for e in enemies.values():
                ex, ey = e[0] - cx, e[1] - cy
                if 0 <= ex < 240 and 0 <= ey < 210:
                    spr += [(int(ex), int(ey), 20, 0), (int(ex) + 8, int(ey), 21, 0)]
            inp = ",".join(
                k
                for k, on in (
                    ("right", held[0] > 0),
                    ("left", held[0] < 0),
                    ("down", held[1] > 0),
                    ("up", held[1] < 0),
                )
                if on
            )
            row = {
                "f": fr,
                "in": inp,
                "oam": oam_hex([(int(x), int(y), t, l) for x, y, t, l in spr]),
            }
            if camera:
                row["sc"] = {
                    "snes.ppu.layers[0].hscroll": int(cx) % 1024,
                    "snes.ppu.layers[0].vscroll": int(cy) % 1024,
                    "snes.ppu.layers[1].hscroll": 0,
                    "snes.ppu.layers[1].vscroll": 0,
                }
            f.write(json.dumps(row) + "\n")
            truth.append((fr / 60, px, py))
    return truth


class OamTests(unittest.TestCase):
    def test_player_and_enemies_from_oam_with_camera(self):
        p = os.path.join(tempfile.mkdtemp(), "s.oam.jsonl")
        truth = make_trace(p)
        frames, meta = telemetry.load_with_meta(p)
        self.assertTrue(meta["camera"])
        self.assertGreater(meta["player_confidence"], 0.5)
        self.assertFalse(meta["events"])
        tt = {round(t, 2): (x, y) for t, x, y in truth}
        xs = [f["px"] for f in frames]
        ys = [f["py"] for f in frames]
        tx = [tt[f["t"]][0] for f in frames]
        ty = [tt[f["t"]][1] for f in frames]
        self.assertGreater(oam._corr(xs, tx), 0.99)
        self.assertGreater(oam._corr(ys, ty), 0.99)
        self.assertGreater(
            sum(1 for f in frames if f["enemies"]), len(frames) * 0.2
        )  # HUD não vira inimigo, inimigos aparecem

    def test_metrics_and_genome_from_oam(self):
        p = os.path.join(tempfile.mkdtemp(), "s.oam.jsonl")
        make_trace(p)
        frames, meta = telemetry.load_with_meta(p)
        m = extract(frames, meta=meta)
        self.assertAlmostEqual(m["player_speed"], 72, delta=12)  # 1.2 px/frame * 60
        self.assertIsNone(m["rewards_per_min"])
        g = genome.validate(build_genome(m, "sim"))
        self.assertEqual(g["provenance"]["raw.rewards_per_min"], "unavailable")
        self.assertTrue(
            validate.validate_map(generate.generate(g, seed=2), g)["passed"]
        )

    def test_render_observer_template(self):
        s = auto.render(
            "C:\\x\\a.jsonl", mode="bot", seconds=120, seed=4, skip_title=True
        )
        self.assertNotIn("__", s)
        self.assertIn("C:/x/a.jsonl", s)
        self.assertIn("seconds = 120", s)
