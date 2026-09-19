import pytest

from fleet import find_conflict, plan_fleet
from heuristics import combined_heuristic, furthest_item, span_heuristic
from layouts import generate_warehouse
from problem import PickupProblem
from search import a_star_search, uniform_cost_search


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("heuristic", [furthest_item, span_heuristic, combined_heuristic])
def test_a_star_matches_ucs(seed, heuristic):
    problem = PickupProblem(generate_warehouse(25, 13, 5, seed))
    assert a_star_search(problem, heuristic).cost == uniform_cost_search(problem).cost


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("method", ["prioritized", "cbs"])
def test_fleet_plans_are_valid(seed, method):
    warehouse = generate_warehouse(25, 13, 8, seed, num_robots=3)
    result = plan_fleet(warehouse, method, strategy="round_robin")
    assert result is not None
    assert find_conflict(result.paths) is None

    for start, path, items in zip(warehouse.starts, result.paths, result.assignment):
        assert path[0] == start
        assert set(items) <= set(path)
        for a, b in zip(path, path[1:]):
            assert warehouse.is_passable(b)
            assert abs(a[0] - b[0]) + abs(a[1] - b[1]) <= 1


@pytest.mark.parametrize("seed", range(8))
def test_cbs_bounds(seed):
    warehouse = generate_warehouse(25, 13, 8, seed, num_robots=3)
    independent = plan_fleet(warehouse, "independent", strategy="round_robin")
    prioritized = plan_fleet(warehouse, "prioritized", strategy="round_robin")
    cbs = plan_fleet(warehouse, "cbs", strategy="round_robin")
    assert independent.total_cost <= cbs.total_cost <= prioritized.total_cost
