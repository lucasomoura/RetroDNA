"""Estatística mínima compartilhada (sem dependências)."""

import statistics


def pearson(a: list[float], b: list[float]) -> float | None:
    """Correlação de Pearson; None se não for definida (poucos pontos ou variância zero)."""
    if len(a) < 3 or len(a) != len(b):
        return None
    if statistics.pstdev(a) == 0 or statistics.pstdev(b) == 0:
        return None
    ma, mb = statistics.mean(a), statistics.mean(b)
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return cov / (len(a) * statistics.pstdev(a) * statistics.pstdev(b))
