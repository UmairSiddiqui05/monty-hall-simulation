"""
Core Monty Hall simulation engine.

All simulations are vectorized with NumPy, so millions of games run in seconds.
Each function returns a boolean array where True means the contestant won the car.
Doors are numbered 0, 1, 2.
"""
from __future__ import annotations

import numpy as np


def host_opens(car: np.ndarray, pick: np.ndarray,
               rng: np.random.Generator) -> np.ndarray:
    """Door the (knowing) host opens in the classic 3-door game.

    The host never opens the contestant's door and never reveals the car.
    If the contestant picked the car, the host chooses between the two
    goat doors uniformly at random.
    """
    opened = np.empty(car.shape[0], dtype=int)
    same = car == pick
    # Contestant picked a goat: host is FORCED to open the only other goat.
    # (Doors 0+1+2 = 3, so the third door is 3 - a - b.)
    opened[~same] = 3 - car[~same] - pick[~same]
    # Contestant picked the car: host picks one of the two goats at random.
    offset = rng.integers(1, 3, same.sum())          # 1 or 2
    opened[same] = (pick[same] + offset) % 3
    return opened


def play_classic(n_games: int, strategy: str, seed: int | None = None) -> np.ndarray:
    """Play the standard 3-door game with a host who knows where the car is.

    strategy: 'stay', 'switch', or 'random' (flip a coin after the reveal).
    """
    rng = np.random.default_rng(seed)
    car = rng.integers(0, 3, n_games)
    pick = rng.integers(0, 3, n_games)
    opened = host_opens(car, pick, rng)
    other = 3 - pick - opened                    # the one door left closed

    if strategy == "stay":
        final = pick
    elif strategy == "switch":
        final = other
    elif strategy == "random":
        final = np.where(rng.random(n_games) < 0.5, other, pick)
    else:
        raise ValueError(f"unknown strategy: {strategy}")
    return final == car


def play_n_doors(n_games: int, n_doors: int, strategy: str,
                 seed: int | None = None) -> np.ndarray:
    """Generalized game: the host opens n_doors - 2 goat doors, leaving one other.

    If you picked the car, the leftover door is a random goat.
    If you picked a goat, the leftover door MUST be the car.
    So switching wins exactly when your first pick was wrong.
    """
    rng = np.random.default_rng(seed)
    car = rng.integers(0, n_doors, n_games)
    pick = rng.integers(0, n_doors, n_games)
    first_pick_right = car == pick
    if strategy == "stay":
        return first_pick_right
    if strategy == "switch":
        return ~first_pick_right
    raise ValueError(f"unknown strategy: {strategy}")


def play_ignorant_host(n_games: int, strategy: str,
                       seed: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """'Monty Fall' variant: the host does NOT know where the car is.

    He opens one of the two unpicked doors at random. Sometimes he
    accidentally reveals the car; those games are thrown out.

    Returns (wins, valid), where valid marks games in which a goat was shown.
    """
    rng = np.random.default_rng(seed)
    car = rng.integers(0, 3, n_games)
    pick = rng.integers(0, 3, n_games)
    opened = (pick + rng.integers(1, 3, n_games)) % 3
    other = 3 - pick - opened
    valid = opened != car
    final = pick if strategy == "stay" else other
    return final == car, valid
