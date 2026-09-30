"""Regras de consistência do Design Genome que envolvem mais de um campo (RFC 0001)."""

PACING_TOLERANCE = 0.30


def pacing_issues(pacing: dict, encounters: int) -> list[str]:
    """between_encounters deve valer ~ exploration + combat (tolerância de 30%)."""
    if encounters < 3:
        return []
    total = pacing["average_exploration_time_s"] + pacing["average_combat_duration_s"]
    interval = pacing["average_time_between_encounters_s"]
    if abs(interval - total) > PACING_TOLERANCE * interval:
        return [
            (
                "pacing incoerente: intervalo entre encontros "
                f"({interval}s) != exploração + combate ({total:.1f}s), tolerância ±30%"
            )
        ]
    return []
