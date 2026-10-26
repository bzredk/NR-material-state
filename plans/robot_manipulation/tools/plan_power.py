"""Compute planning approximations, never experimental observations.

Uses only the Python standard library. The paired-binary approximation uses
discordance d and the null variance d / n. It ignores continuity correction,
heterogeneous clusters, and model-training variation. Final sizing requires
the independent pilot specified in protocol.md.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=root / "eval_spec.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    stats = spec["statistics"]
    compute = spec["compute_budget"]
    dataset = next(item for item in spec["datasets"] if item["name"] == "robot_3d")
    alpha = stats["alpha_two_sided"]
    power = stats["planning_power"]
    discordance = stats["planning_discordance"]
    if not (0 < alpha < 1 and 0 < power < 1 and 0 < discordance <= 1):
        raise ValueError("Invalid probability in planning specification")
    normal = NormalDist()
    quantile_sum = normal.inv_cdf(1 - alpha / 2) + normal.inv_cdf(power)
    sample_sizes = []
    for difference in stats["planning_effects"]:
        if not 0 < difference <= discordance:
            raise ValueError("Effect must be positive and no larger than discordance")
        count = math.ceil(discordance * quantile_sum**2 / difference**2)
        sample_sizes.append({"absolute_difference": difference, "approx_independent_units": count})

    pairs = dataset["matched_pair_blocks"]
    singles = dataset["natural_history_blocks"]
    if pairs + singles != dataset["provisional_test_blocks"]:
        raise ValueError("History populations do not sum to the planned test size")
    seed_count = len(spec["seeds"])
    instances = compute["trained_method_families"] * seed_count + compute["deterministic_method_instances"]
    episodes = instances * (2 * pairs + singles)
    simulated_hours = episodes * compute["assumed_episode_seconds_excluding_preconditioning"] / 3600
    worker_hours = simulated_hours / compute["illustrative_realtime_factor"]
    result = {
        "status": "planning_arithmetic_not_experimental_results",
        "formula": "ceil(d * (z_(1-alpha/2) + z_power)^2 / delta^2)",
        "assumptions": {"alpha_two_sided": alpha, "power": power, "discordance": discordance},
        "sample_size_approximations": sample_sizes,
        "provisional_primary_natural_history_blocks": singles,
        "provisional_matched_mechanism_blocks": pairs,
        "evaluated_method_instances": instances,
        "base_evaluation_episodes": episodes,
        "simulated_hours_excluding_preconditioning": simulated_hours,
        "illustrative_solver_worker_hours": worker_hours,
        "ideal_wall_hours_with_independent_workers": worker_hours / compute["illustrative_independent_workers"],
        "budget_exclusions": compute["exclusions"],
        "limitations": [
            "Approximation does not include clustering, training-seed variation, or continuity correction.",
            "Natural and matched populations must not be pooled to inflate primary sample size.",
            "Safety noninferiority and per-stratum inference require separate power assessment.",
            "Throughput and worker independence are unmeasured assumptions.",
        ],
    }
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
