"""
Run every experiment, then save raw results to data/ and charts to figures/.

Usage (from the repo root):
    python src/run_experiments.py
    python src/run_experiments.py --games 1000000 --seed 7
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from monty_hall import play_classic, play_ignorant_host, play_n_doors

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIGS = ROOT / "figures"

STAY_C, SWITCH_C, RAND_C, GREY = "#E4572E", "#29335C", "#A0A4B8", "#6B6B6B"
plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130, "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlesize": 13,
})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIGS / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved figures/{name}")


def exp_head_to_head(n, seed):
    """Experiment 1: stay vs switch vs coin flip."""
    rows = []
    for i, s in enumerate(["stay", "switch", "random"]):
        w = play_classic(n, s, seed + i)
        rows.append({"strategy": s, "games": n, "wins": int(w.sum()),
                     "win_rate": w.mean()})
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "01_head_to_head.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(["Always stay", "Always switch", "Coin flip"], df.win_rate,
                  color=[STAY_C, SWITCH_C, RAND_C], width=0.6)
    for b, r in zip(bars, df.win_rate):
        ax.text(b.get_x() + b.get_width() / 2, r + 0.015, f"{r:.1%}",
                ha="center", weight="bold")
    for y, lbl in [(1/3, "1/3"), (1/2, "1/2"), (2/3, "2/3")]:
        ax.axhline(y, ls=":", color=GREY, lw=1)
        ax.text(2.45, y, lbl, va="center", color=GREY, fontsize=9)
    ax.set_ylim(0, 0.8)
    ax.set_ylabel("Win rate")
    ax.set_title(f"Switching doubles your chances ({n:,} games per strategy)")
    save(fig, "01_head_to_head.png")
    return df


def exp_convergence(n, seed):
    """Experiment 2: running win rate as games accumulate."""
    n = min(n, 10_000)
    stay = play_classic(n, "stay", seed)
    switch = play_classic(n, "switch", seed + 1)
    idx = np.arange(1, n + 1)
    df = pd.DataFrame({"game": idx,
                       "stay_running_rate": np.cumsum(stay) / idx,
                       "switch_running_rate": np.cumsum(switch) / idx})
    df.to_csv(DATA / "02_convergence.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(idx, df.switch_running_rate, color=SWITCH_C, label="Switch")
    ax.plot(idx, df.stay_running_rate, color=STAY_C, label="Stay")
    ax.axhline(2/3, ls="--", color=SWITCH_C, alpha=.5)
    ax.axhline(1/3, ls="--", color=STAY_C, alpha=.5)
    ax.set_xscale("log")
    ax.set_ylim(0, 1)
    ax.set_xlabel("Number of games played (log scale)")
    ax.set_ylabel("Running win rate")
    ax.set_title("Early noise fades: win rates settle at 2/3 and 1/3")
    ax.legend(loc="upper right", frameon=False)
    save(fig, "02_convergence.png")
    return df


def exp_outcome_breakdown(n, seed):
    """Experiment 3: split games by whether the first pick was right."""
    rng = np.random.default_rng(seed)
    right = rng.integers(0, 3, n) == rng.integers(0, 3, n)
    df = pd.DataFrame({
        "first_pick": ["car", "goat"],
        "share_of_games": [right.mean(), (~right).mean()],
        "stay_result": ["win", "lose"],
        "switch_result": ["lose", "win"],
    })
    df.to_csv(DATA / "03_outcome_breakdown.csv", index=False)

    fig, ax = plt.subplots(figsize=(9, 3.2))
    a, b = right.mean(), (~right).mean()
    ax.barh([0], [a], color=STAY_C, height=0.5)
    ax.barh([0], [b], left=[a], color=SWITCH_C, height=0.5)
    ax.text(a / 2, 0, f"First pick = CAR\n{a:.1%}\nstaying wins",
            ha="center", va="center", color="white", weight="bold")
    ax.text(a + b / 2, 0, f"First pick = GOAT\n{b:.1%}\nhost must show the other goat,\n"
            "so switching wins", ha="center", va="center", color="white", weight="bold")
    ax.set_xlim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("Share of all games")
    ax.set_title("Switching wins whenever your first guess was wrong")
    ax.spines["left"].set_visible(False)
    save(fig, "03_outcome_breakdown.png")
    return df


def exp_n_doors(n, seed):
    """Experiment 4: generalize to N doors."""
    rows = []
    for d in [3, 4, 5, 10, 20, 50, 100]:
        sw = play_n_doors(n, d, "switch", seed + d)
        rows.append({"doors": d, "stay_win_rate": 1 - sw.mean(),
                     "switch_win_rate": sw.mean(), "theory_switch": (d - 1) / d})
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "04_n_doors.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(df))
    ax.bar(x - 0.2, df.stay_win_rate, 0.4, color=STAY_C, label="Stay")
    ax.bar(x + 0.2, df.switch_win_rate, 0.4, color=SWITCH_C, label="Switch")
    ax.plot(x + 0.2, df.theory_switch, "o", color="gold", mec="black",
            label="Theory: (N−1)/N")
    ax.set_xticks(x, df.doors)
    ax.set_xlabel("Number of doors (host opens all but one of the others)")
    ax.set_ylabel("Win rate")
    ax.set_ylim(0, 1.1)
    ax.set_title("More doors make the answer obvious")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    save(fig, "04_n_doors.png")
    return df


def exp_ignorant_host(n, seed):
    """Experiment 5: knowing host vs a host who opens doors at random."""
    rows = []
    for i, s in enumerate(["stay", "switch"]):
        w = play_classic(n, s, seed + i)
        rows.append({"host": "Knowing host (classic)", "strategy": s,
                     "valid_games": n, "win_rate": w.mean()})
    for i, s in enumerate(["stay", "switch"]):
        w, v = play_ignorant_host(n, s, seed + 10 + i)
        rows.append({"host": "Ignorant host", "strategy": s,
                     "valid_games": int(v.sum()), "win_rate": w[v].mean()})
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "05_ignorant_host.csv", index=False)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    hosts = df.host.unique()
    x = np.arange(len(hosts))
    for off, s, c in [(-0.2, "stay", STAY_C), (0.2, "switch", SWITCH_C)]:
        vals = df[df.strategy == s].win_rate.values
        bars = ax.bar(x + off, vals, 0.4, color=c, label=s.title())
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.015, f"{v:.1%}",
                    ha="center", weight="bold")
    ax.set_xticks(x, hosts)
    ax.set_ylim(0, 0.8)
    ax.set_ylabel("Win rate (games where a goat was shown)")
    ax.set_title("The host's knowledge is what creates the edge")
    ax.legend(frameon=False)
    save(fig, "05_ignorant_host.png")
    return df


def exp_short_run_variance(seed, sessions=5000, games_per=30):
    """Experiment 6: what a real person playing only 30 games would see."""
    stay = play_classic(sessions * games_per, "stay", seed).reshape(sessions, games_per).sum(1)
    switch = play_classic(sessions * games_per, "switch", seed + 1).reshape(sessions, games_per).sum(1)
    df = pd.DataFrame({"session": np.arange(sessions),
                       "stay_wins": stay, "switch_wins": switch})
    df.to_csv(DATA / "06_short_run_sessions.csv", index=False)
    pct = (switch > stay).mean()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bins = np.arange(-0.5, games_per + 1.5)
    ax.hist(stay, bins=bins, color=STAY_C, alpha=0.75, label="Stay")
    ax.hist(switch, bins=bins, color=SWITCH_C, alpha=0.75, label="Switch")
    ax.set_xlabel(f"Cars won out of {games_per} games")
    ax.set_ylabel(f"Number of players (out of {sessions:,})")
    ax.set_title(f"Even over {games_per} games, a switcher beats a stayer "
                 f"{pct:.0%} of the time")
    ax.legend(frameon=False)
    save(fig, "06_short_run_variance.png")
    return df, pct


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--games", type=int, default=100_000,
                   help="games per strategy per experiment (default 100,000)")
    p.add_argument("--seed", type=int, default=42, help="random seed (default 42)")
    a = p.parse_args()
    DATA.mkdir(exist_ok=True)
    FIGS.mkdir(exist_ok=True)

    print(f"Running experiments with {a.games:,} games, seed={a.seed}\n")
    print("[1] Stay vs switch vs coin flip"); r1 = exp_head_to_head(a.games, a.seed)
    print("[2] Convergence over time");       exp_convergence(a.games, a.seed)
    print("[3] Why switching works");         r3 = exp_outcome_breakdown(a.games, a.seed)
    print("[4] N-door generalization");       r4 = exp_n_doors(a.games, a.seed)
    print("[5] Ignorant host variant");       r5 = exp_ignorant_host(a.games, a.seed)
    print("[6] Short-run variance");          _, pct = exp_short_run_variance(a.seed)

    fmt = "{:.4f}".format
    print("\n=== RESULTS ===\n")
    print(r1.to_string(index=False, formatters={"win_rate": fmt}), "\n")
    print(r3.to_string(index=False, formatters={"share_of_games": fmt}), "\n")
    print(r4.to_string(index=False, float_format=fmt), "\n")
    print(r5.to_string(index=False, formatters={"win_rate": fmt}), "\n")
    print(f"Switcher beats stayer over 30 games in {pct:.1%} of sessions")


if __name__ == "__main__":
    main()
