"""Controle de qualidade, dispersão, proveniência honesta e validação não circular."""

import json

import pytest

from apps import cli
from apps.generator import generate, validate
from apps.observer import sample
from packages.events import telemetry
from packages.metrics import aggregate, assess, build_genome, extract
from packages.schema import validate as validate_genome


def _frames(tmp_path, seed=7):
    p = tmp_path / f"s{seed}.jsonl"
    sample.make(str(p), seed=seed)
    return telemetry.load(p)


def _still(frames):
    """Mesmas posições de inimigos, mas o jogador não sai do lugar."""
    return [{**f, "px": 100.0, "py": 100.0} for f in frames]


def test_good_session_is_accepted(tmp_path):
    frames = _frames(tmp_path)
    q = assess(frames, {}, extract(frames))
    assert q["accepted"] and not q["reasons"]
    assert q["indicators"]["moving_fraction"] > 0.5


def test_stationary_player_is_rejected(tmp_path):
    frames = _still(_frames(tmp_path))
    q = assess(frames, {}, extract(frames))
    assert not q["accepted"]
    assert any("parado" in r for r in q["reasons"])


def test_low_player_confidence_is_rejected(tmp_path):
    frames = _frames(tmp_path)
    q = assess(frames, {"source": "oam", "player_confidence": 0.05}, extract(frames))
    assert not q["accepted"]
    assert any("confiança" in r for r in q["reasons"])


def test_short_session_is_rejected(tmp_path):
    frames = _frames(tmp_path)[:100]  # ~10 s a 10 Hz
    q = assess(frames, {}, extract(frames))
    assert not q["accepted"]
    assert any("curta" in r for r in q["reasons"])


def test_cli_excludes_rejected_session_and_writes_quality_json(tmp_path, capsys):
    good = [_frames(tmp_path, s) for s in (7, 11)]
    paths = []
    for i, frames in enumerate(good):
        p = tmp_path / f"good{i}.jsonl"
        p.write_text("\n".join(json.dumps(f) for f in frames), encoding="utf-8")
        paths.append(p)
    bad = tmp_path / "bad.jsonl"
    bad.write_text("\n".join(json.dumps(f) for f in _still(good[0])), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    gn = cli._genome_from([*paths, bad], "teste", out)
    assert gn["source"]["sessions"] == 2
    assert "REJEITADA bad.jsonl" in capsys.readouterr().out
    quality = json.loads((out / "quality.json").read_text(encoding="utf-8"))
    assert [q["accepted"] for q in quality] == [True, True, False]


def test_cli_fails_when_every_session_is_rejected(tmp_path):
    frames = _still(_frames(tmp_path))
    p = tmp_path / "bad.jsonl"
    p.write_text("\n".join(json.dumps(f) for f in frames), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    with pytest.raises(SystemExit, match="controle de qualidade"):
        cli._genome_from([p], "teste", out)


def test_aggregate_reports_dispersion_only_with_two_sessions(tmp_path):
    ms = [extract(_frames(tmp_path, s)) for s in (7, 11, 5)]
    assert "dispersion" not in aggregate(ms[:1])
    agg = aggregate(ms)
    assert set(agg["dispersion"]) >= {"player_speed", "combat_ratio", "encounters"}
    g = validate_genome(build_genome(agg, "teste"))
    assert g["dispersion"]["player_speed"] >= 0


def test_pacing_provenance_is_unavailable_without_encounters(tmp_path):
    frames = [{**f, "enemies": []} for f in _frames(tmp_path)]
    m = extract(frames)
    assert m["encounters"] == 0
    g = build_genome(m, "teste")
    for key in (
        "pacing.average_exploration_time_s",
        "pacing.average_time_between_encounters_s",
        "pacing.average_combat_duration_s",
    ):
        assert g["provenance"][key] == "unavailable"


def test_pacing_aggregate_ignores_sessions_without_encounters(tmp_path):
    with_enc = extract(_frames(tmp_path))
    none = extract([{**f, "enemies": []} for f in _frames(tmp_path)])
    agg = aggregate([with_enc, none])
    assert agg["exploration_time_s"] == with_enc["exploration_time_s"]
    assert agg["encounter_interval_s"] == with_enc["encounter_interval_s"]


def test_combat_and_exploration_are_inferred_not_measured(tmp_path):
    g = build_genome(extract(_frames(tmp_path)), "teste")
    assert g["provenance"]["gameplay.combat"] == "inferred"
    assert g["provenance"]["gameplay.exploration"] == "inferred"


def test_validator_does_not_compare_against_generator_defaults(tmp_path):
    g = validate_genome(build_genome(extract(_frames(tmp_path)), "teste"))
    g["raw"]["objectives_per_min"] = None
    g["raw"]["rewards_per_min"] = None
    m = generate.generate(g, seed=1, minutes=4)
    result = validate.validate_map(m, g)
    by_name = {c["check"]: c for c in result["checks"]}
    for name in ("objetivos (NPCs)", "recompensas (itens)"):
        assert by_name[name]["level"] == "n/a"
        assert by_name[name]["expected"] == "n/a"
    assert "| n/a |" in validate.to_markdown(result)
