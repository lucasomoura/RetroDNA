"""Taxas padrão do GERADOR (não fazem parte do Genome).

Quando o Genome não tem a taxa (dado `unavailable`, ex.: OAM não vê eventos), o gerador usa
um valor padrão para ter o que gerar. Esse valor é uma escolha de design, não uma medição,
e por isso o validador não o usa como alvo (ver `apps/generator/validate.py`).
"""

DEFAULT_RATES = {"objectives_per_min": 1.0, "rewards_per_min": 2.0}


def measured_rate(g: dict, key: str) -> float | None:
    """Taxa por minuto medida no Genome, ou None quando indisponível."""
    return g["raw"].get(key)


def rate(g: dict, key: str) -> float:
    """Taxa para GERAR: a medida, ou o padrão do gerador quando indisponível."""
    v = measured_rate(g, key)
    return DEFAULT_RATES[key] if v is None else v
