"""Sanity checks: simulated rates must land near the known answers."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from monty_hall import host_opens, play_classic, play_ignorant_host, play_n_doors  # noqa: E402

N, TOL = 200_000, 0.01


def test_stay_is_one_third():
    assert abs(play_classic(N, "stay", 1).mean() - 1/3) < TOL


def test_switch_is_two_thirds():
    assert abs(play_classic(N, "switch", 2).mean() - 2/3) < TOL


def test_coin_flip_is_half():
    assert abs(play_classic(N, "random", 3).mean() - 1/2) < TOL


def test_n_doors_matches_theory():
    for d in (4, 10, 100):
        assert abs(play_n_doors(N, d, "switch", d).mean() - (d - 1) / d) < TOL


def test_ignorant_host_is_fifty_fifty():
    w, v = play_ignorant_host(N, "switch", 4)
    assert abs(w[v].mean() - 1/2) < TOL


def test_host_never_reveals_car_or_pick():
    rng = np.random.default_rng(0)
    car, pick = rng.integers(0, 3, N), rng.integers(0, 3, N)
    opened = host_opens(car, pick, rng)
    assert not np.any(opened == car)
    assert not np.any(opened == pick)
