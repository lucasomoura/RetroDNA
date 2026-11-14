import json

import pytest
from test_oam import oam_hex

from apps.cli import main
from apps.observer import calibrate


def write_session(path, phases):
    """phases: lista de (segundos, n_sprites). Amostras a 10 Hz."""
    frame, rows = 0, [{"meta": {"source": "oam"}}]
    for seconds, n in phases:
        for _ in range(int(seconds * 10)):
            frame += 6
            sprites = [(10 + 16 * i, 40, 1, 0) for i in range(n)]
            rows.append({"f": frame, "in": "", "oam": oam_hex(sprites)})
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


def test_visible_count_matches_lua_rule():
    from packages.events.oam import visible_count

    assert visible_count(oam_hex([(10, 40, 1, 0)] * 5)) == 5
    assert visible_count(oam_hex([])) == 0  # sprites escondidos em y=240


def test_suggests_threshold_between_menus_and_gameplay(tmp_path):
    p = tmp_path / "humano.jsonl"
    write_session(
        p, [(6, 40), (14, 3), (10, 2), (30, 15)]
    )  # boot (ignorado), menus, jogo
    res = calibrate.analyze(p, gameplay_from=30)
    assert res["separable"] and 3 < res["threshold"] <= 15
    assert res["menu_p95"] <= 3 and res["game_p5"] >= 15


def test_reports_when_counts_overlap(tmp_path):
    p = tmp_path / "humano.jsonl"
    write_session(p, [(6, 40), (20, 14), (30, 15)])
    res = calibrate.analyze(p, gameplay_from=26)
    assert not res["separable"]
    assert "NÃO separável" in calibrate.format_report(res)


def test_timeline_without_gameplay_from_and_cli(tmp_path, capsys):
    p = tmp_path / "humano.jsonl"
    write_session(p, [(10, 2), (20, 18)])
    assert main(["calibrate", str(p)]) == 0
    out = capsys.readouterr().out
    assert "--gameplay-from" in out
    assert main(["calibrate", str(p), "--gameplay-from", "10"]) == 0
    assert "--gameplay-sprites" in capsys.readouterr().out


def test_too_short_session_is_rejected(tmp_path):
    p = tmp_path / "x.jsonl"
    write_session(p, [(1, 5)])
    with pytest.raises(ValueError, match="curta demais"):
        calibrate.analyze(p)
