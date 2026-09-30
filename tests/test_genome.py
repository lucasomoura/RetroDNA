from packages.schema.genome import Gameplay


def test_gameplay_ratio():
    gameplay = Gameplay(
        exploration=0.72,
        combat=0.28,
        objective_density=0.5,
        enemy_density=0.3,
        reward_frequency=0.4,
    )
    assert gameplay.exploration == 0.72