import argparse
import time

from fleet import plan_fleet
from heuristics import combined_heuristic, furthest_item, span_heuristic
from layouts import generate_warehouse
from problem import PickupProblem
from search import a_star_search, breadth_first_search, uniform_cost_search

HEURISTICS = {
    "furthest": furthest_item,
    "span": span_heuristic,
    "combined": combined_heuristic,
}


def run_single(args):
    warehouse = generate_warehouse(
        args.width, args.height, args.items, args.seed, cross_aisle=args.cross_aisle
    )
    problem = PickupProblem(warehouse)

    start = time.time()
    if args.algo == "astar":
        result = a_star_search(problem, HEURISTICS[args.heuristic])
    elif args.algo == "ucs":
        result = uniform_cost_search(problem)
    else:
        result = breadth_first_search(problem)
    elapsed = time.time() - start

    print(warehouse.render(problem.path_positions(result.actions)))
    print("Path found with total cost of %d in %.3f seconds" % (result.cost, elapsed))
    print("Search nodes expanded: %d" % result.expanded)


def run_fleet(args):
    warehouse = generate_warehouse(
        args.width,
        args.height,
        args.items,
        args.seed,
        num_robots=args.robots,
        cross_aisle=args.cross_aisle,
    )
    result = plan_fleet(warehouse, args.planner, strategy=args.assignment)

    if result is None:
        print("No conflict-free plan found within the search limits")
        return

    print(warehouse.render_fleet(result.paths))
    for robot, path in enumerate(result.paths):
        print(
            "Robot %d: %d items, cost %d, done at t=%d"
            % (robot, len(result.assignment[robot]), result.costs[robot], len(path) - 1)
        )
    print("Total cost %d, makespan %d" % (result.total_cost, result.makespan))
    print(
        "Planned in %.3f seconds, %d high-level nodes, %d low-level expansions"
        % (result.elapsed, result.nodes, result.expanded)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=25)
    parser.add_argument("--height", type=int, default=13)
    parser.add_argument("--items", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--cross-aisle", type=int, default=6)
    parser.add_argument("--robots", type=int, default=1)
    parser.add_argument("--planner", choices=["independent", "prioritized", "cbs"], default="cbs")
    parser.add_argument("--assignment", choices=["greedy", "round_robin"], default="greedy")
    parser.add_argument("--algo", choices=["astar", "ucs", "bfs"], default="astar")
    parser.add_argument("--heuristic", choices=list(HEURISTICS), default="combined")
    args = parser.parse_args()

    if args.robots > 1:
        run_fleet(args)
    else:
        run_single(args)


if __name__ == "__main__":
    main()
