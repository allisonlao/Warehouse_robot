from fleet import find_conflict, plan_fleet
from layouts import generate_warehouse

METHODS = ["independent", "prioritized", "cbs"]


def run_fleet_benchmark(
    seeds=range(10),
    robot_counts=(2, 3),
    num_items=8,
    width=25,
    height=13,
    strategy="greedy",
    cross_aisle=6,
    time_limit=5,
):
    baseline = {}
    for seed in seeds:
        single = generate_warehouse(width, height, num_items, seed, cross_aisle=cross_aisle)
        baseline[seed] = plan_fleet(single, "independent", strategy=strategy).makespan

    print("assignment: %s, items: %d, seeds: %d" % (strategy, num_items, len(list(seeds))))
    for robots in robot_counts:
        stats = {m: dict(solved=0, cost=0, makespan=0, expanded=0, elapsed=0.0) for m in METHODS}
        conflicting = 0
        speedups = []

        for seed in seeds:
            warehouse = generate_warehouse(
                width, height, num_items, seed, num_robots=robots, cross_aisle=cross_aisle
            )
            results = {
                m: plan_fleet(warehouse, m, strategy=strategy, time_limit=time_limit)
                for m in METHODS
            }

            if find_conflict(results["independent"].paths) is not None:
                conflicting += 1

            for method, result in results.items():
                if result is None:
                    continue
                if method != "independent":
                    assert find_conflict(result.paths) is None
                entry = stats[method]
                entry["solved"] += 1
                entry["cost"] += result.total_cost
                entry["makespan"] += result.makespan
                entry["expanded"] += result.expanded
                entry["elapsed"] += result.elapsed
                if method == "cbs":
                    speedups.append(baseline[seed] / result.makespan)

        print("\n%d robots, independent plans conflicted in %d/%d layouts" % (robots, conflicting, len(list(seeds))))
        print("%-12s %7s %9s %9s %10s %8s" % ("planner", "solved", "avg cost", "makespan", "expanded", "avg sec"))
        for method in METHODS:
            entry = stats[method]
            n = max(entry["solved"], 1)
            print(
                "%-12s %4d/%-2d %9.1f %9.1f %10.0f %8.3f"
                % (
                    method,
                    entry["solved"],
                    len(list(seeds)),
                    entry["cost"] / n,
                    entry["makespan"] / n,
                    entry["expanded"] / n,
                    entry["elapsed"] / n,
                )
            )
        if speedups:
            print("makespan speedup vs 1 robot (CBS): %.2fx" % (sum(speedups) / len(speedups)))


if __name__ == "__main__":
    run_fleet_benchmark(strategy="greedy")
    print()
    run_fleet_benchmark(strategy="round_robin")
