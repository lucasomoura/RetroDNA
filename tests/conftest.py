import pytest

from apps.observer import sample
from packages.events import telemetry
from packages.metrics import aggregate, build_genome, extract
from packages.schema import Genome, validate


@pytest.fixture(scope="session")
def genome(tmp_path_factory):
    """Genome v0.2 real, extraído de 3 sessões de telemetria sintética."""
    d = tmp_path_factory.mktemp("sessions")
    ms = []
    for seed in (7, 11, 5):
        path = d / f"s{seed}.jsonl"
        sample.make(str(path), seed=seed)
        ms.append(extract(telemetry.load(path)))
    return Genome.model_validate(validate(build_genome(aggregate(ms), "teste")))
