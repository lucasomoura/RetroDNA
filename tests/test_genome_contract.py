"""Contrato do Design Genome (RFC 0001): campos, proveniência, faixas e consistência."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from packages.schema import Genome, validate

ROOT = Path(__file__).parent.parent


def test_exploration_and_combat_sum_to_one(genome):
    assert genome.gameplay.exploration + genome.gameplay.combat == pytest.approx(1)


def test_every_field_has_provenance(genome):
    assert genome.provenance["tension.curve"] == "hypothesis"
    assert genome.provenance["level_design.open_area_frequency"] == "unavailable"


def test_rejects_out_of_range(genome):
    bad = genome.model_dump()
    bad["gameplay"]["combat"] = 1.5
    with pytest.raises(ValidationError):
        Genome.model_validate(bad)


def test_rejects_incoherent_pacing(genome):
    bad = genome.model_dump()
    bad["pacing"]["average_time_between_encounters_s"] = 500
    with pytest.raises(ValueError):
        validate(bad)


def test_rejects_unknown_fields(genome):
    bad = genome.model_dump()
    bad["surprise"] = 1
    with pytest.raises(ValidationError):
        Genome.model_validate(bad)


def test_committed_json_schema_is_in_sync():
    path = ROOT / "docs" / "genome" / "genome.schema.json"
    assert json.loads(path.read_text(encoding="utf-8")) == Genome.model_json_schema()


def test_example_genome_is_valid():
    path = ROOT / "examples" / "genome.sintetico.json"
    Genome.model_validate(json.loads(path.read_text(encoding="utf-8")))
