import json
import os
import tempfile
import unittest

from apps.analyzer import report as analyze
from apps.generator import generate, validate
from apps.observer import sample
from packages.events import telemetry
from packages.metrics import aggregate, build_genome, extract
from packages.schema import genome


def make_genome(seeds=(7, 11, 5)):
    d = tempfile.mkdtemp()
    ms = []
    for s in seeds:
        p = os.path.join(d, f"s{s}.jsonl")
        sample.make(p, seed=s)
        ms.append(extract(telemetry.load(p)))
    return genome.validate(build_genome(aggregate(ms), "teste"))


class Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = make_genome()

    def test_metrics_sane(self):
        p = os.path.join(tempfile.mkdtemp(), "a.jsonl")
        sample.make(p)
        m = extract(telemetry.load(p))
        self.assertGreater(m["player_speed"], 30)
        self.assertEqual(len(m["tension_curve"]), 8)
        self.assertTrue(all(0 <= v <= 1 for v in m["tension_curve"]))
        self.assertGreater(m["encounters"], 3)

    def test_genome_provenance_and_version(self):
        self.assertEqual(self.g["genome_version"], "0.2")
        self.assertEqual(self.g["provenance"]["tension.curve"], "hypothesis")
        self.assertEqual(
            self.g["provenance"]["level_design.open_area_frequency"], "unavailable"
        )
        self.assertEqual(self.g["source"]["sessions"], 3)

    def test_genome_rejects_bad_pacing(self):
        bad = json.loads(json.dumps(self.g))
        bad["pacing"]["average_time_between_encounters_s"] = 500
        with self.assertRaises(ValueError):
            genome.validate(bad)

    def test_no_area_data_marks_unavailable(self):
        p = os.path.join(tempfile.mkdtemp(), "a.jsonl")
        sample.make(p)
        fr = [{k: v for k, v in f.items() if k != "area"} for f in telemetry.load(p)]
        g = build_genome(extract(fr))
        self.assertIsNone(g["level_design"]["alternate_routes"])
        self.assertEqual(
            g["provenance"]["level_design.alternate_routes"], "unavailable"
        )

    def test_generation_deterministic(self):
        a = generate.generate(self.g, seed=4)
        b = generate.generate(self.g, seed=4)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_generated_maps_validate(self):
        for theme in generate.THEMES:
            for seed in range(1, 8):
                m = generate.generate(self.g, theme=theme, seed=seed)
                v = validate.validate_map(m, self.g)
                self.assertTrue(
                    v["passed"], (theme, seed, [c for c in v["checks"] if not c["ok"]])
                )

    def test_validator_detects_broken_map(self):
        m = generate.generate(self.g, seed=2)
        m["enemies"] = m["enemies"][:2]
        self.assertFalse(validate.validate_map(m, self.g)["passed"])

    def test_report_has_three_sections(self):
        r = analyze.report(self.g)
        for h in ("## DADO", "## INTERPRETAÇÃO", "## HIPÓTESE"):
            self.assertIn(h, r)
