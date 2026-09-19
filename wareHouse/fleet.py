import heapq
import time
from itertools import count, permutations

from heuristics import manhattan
from spacetime import Constraints, plan_robot


class FleetResult:
    def __init__(self, paths, costs, expanded, nodes):
        self.paths = paths
        self.costs = costs
        self.expanded = expanded
        self.nodes = nodes
        self.assignment = None
        self.elapsed = 0.0

    @property
    def total_cost(self):
        return sum(self.costs)

    @property
    def makespan(self):
        return max(len(path) - 1 for path in self.paths)


def assign_round_robin(warehouse):
    assignment = [[] for _ in warehouse.starts]
    for index, item in enumerate(sorted(warehouse.items)):
        assignment[index % len(warehouse.starts)].append(item)
    return assignment


def assign_items(warehouse, strategy="greedy"):
    if strategy == "round_robin":
        return assign_round_robin(warehouse)

    starts = warehouse.starts
    anchors = list(starts)
    route_length = [0] * len(starts)
    assignment = [[] for _ in starts]
    pending = set(warehouse.items)

    while pending:
        length, robot, item = min(
            (route_length[r] + manhattan(anchors[r], item), r, item)
            for r in range(len(starts))
            for item in pending
        )
        route_length[robot] = length
        anchors[robot] = item
        assignment[robot].append(item)
        pending.remove(item)

    return assignment


def position_at(path, time):
    return path[min(time, len(path) - 1)]


def find_conflict(paths):
    longest = max(len(path) for path in paths)
    for t in range(longest):
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                a_now, b_now = position_at(paths[i], t), position_at(paths[j], t)
                if a_now == b_now:
                    return ("vertex", i, j, a_now, t)
                if t + 1 < longest:
                    a_next, b_next = position_at(paths[i], t + 1), position_at(paths[j], t + 1)
                    if a_now == b_next and b_now == a_next:
                        return ("edge", i, j, a_now, b_now, t)
    return None


def count_conflicts(paths):
    longest = max(len(path) for path in paths)
    total = 0
    for t in range(longest):
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                a_now, b_now = position_at(paths[i], t), position_at(paths[j], t)
                if a_now == b_now:
                    total += 1
                elif t + 1 < longest:
                    a_next, b_next = position_at(paths[i], t + 1), position_at(paths[j], t + 1)
                    if a_now == b_next and b_now == a_next:
                        total += 1
    return total


def conflict_constraints(conflict):
    if conflict[0] == "vertex":
        _, i, j, pos, t = conflict
        return [(i, "vertex", (pos, t)), (j, "vertex", (pos, t))]
    _, i, j, a, b, t = conflict
    return [(i, "edge", (a, b, t + 1)), (j, "edge", (b, a, t + 1))]


def apply_constraint(constraints, kind, data):
    if kind == "vertex":
        constraints.add_vertex(*data)
    else:
        constraints.add_edge(*data)


def plan_independent(warehouse, assignment, horizon=150):
    plans = []
    for robot, start in enumerate(warehouse.starts):
        plan = plan_robot(warehouse, start, assignment[robot], Constraints(), horizon)
        if plan is None:
            return None
        plans.append(plan)
    return FleetResult(
        [p.path for p in plans],
        [p.cost for p in plans],
        sum(p.expanded for p in plans),
        0,
    )


def reserve_path(constraints, path, horizon):
    for t, pos in enumerate(path):
        constraints.add_vertex(pos, t)
    for t in range(len(path), horizon + 1):
        constraints.add_vertex(path[-1], t)
    for t in range(len(path) - 1):
        if path[t] != path[t + 1]:
            constraints.add_edge(path[t + 1], path[t], t + 1)


def prioritized_planning(warehouse, assignment, order, horizon=150):
    starts = warehouse.starts
    plans = [None] * len(starts)
    constraints = Constraints()
    expanded = 0

    for robot in order:
        plan = plan_robot(warehouse, starts[robot], assignment[robot], constraints, horizon)
        if plan is None:
            return None
        plans[robot] = plan
        expanded += plan.expanded
        reserve_path(constraints, plan.path, horizon)

    return FleetResult([p.path for p in plans], [p.cost for p in plans], expanded, 0)


def best_prioritized(warehouse, assignment, horizon=150, max_orders=6):
    orders = list(permutations(range(len(warehouse.starts))))[:max_orders]
    best = None
    expanded = 0
    for order in orders:
        result = prioritized_planning(warehouse, assignment, order, horizon)
        if result is None:
            continue
        expanded += result.expanded
        if best is None or (result.total_cost, result.makespan) < (best.total_cost, best.makespan):
            best = result
    if best is not None:
        best.expanded = expanded
    return best


def conflict_based_search(warehouse, assignment, horizon=150, max_nodes=2000, time_limit=10):
    deadline = time.time() + time_limit
    starts = warehouse.starts
    constraints = [Constraints() for _ in starts]
    plans = []
    expanded = 0

    for robot, start in enumerate(starts):
        plan = plan_robot(warehouse, start, assignment[robot], constraints[robot], horizon)
        if plan is None:
            return None
        plans.append(plan)
        expanded += plan.expanded

    tie_breaker = count()
    root_paths = [p.path for p in plans]
    frontier = [(sum(p.cost for p in plans), count_conflicts(root_paths), next(tie_breaker), constraints, plans)]
    nodes = 0

    while frontier and nodes < max_nodes and time.time() < deadline:
        _, _, _, constraints, plans = heapq.heappop(frontier)
        nodes += 1

        conflict = find_conflict([p.path for p in plans])
        if conflict is None:
            return FleetResult(
                [p.path for p in plans],
                [p.cost for p in plans],
                expanded,
                nodes,
            )

        for robot, kind, data in conflict_constraints(conflict):
            child_constraints = list(constraints)
            child_constraints[robot] = constraints[robot].copy()
            apply_constraint(child_constraints[robot], kind, data)

            plan = plan_robot(
                warehouse, starts[robot], assignment[robot], child_constraints[robot], horizon
            )
            if plan is None:
                continue
            expanded += plan.expanded

            child_plans = list(plans)
            child_plans[robot] = plan
            heapq.heappush(
                frontier,
                (
                    sum(p.cost for p in child_plans),
                    count_conflicts([p.path for p in child_plans]),
                    next(tie_breaker),
                    child_constraints,
                    child_plans,
                ),
            )

    return None


def plan_fleet(warehouse, method="cbs", horizon=150, strategy="greedy", time_limit=10):
    assignment = assign_items(warehouse, strategy)
    start = time.time()

    if method == "independent":
        result = plan_independent(warehouse, assignment, horizon)
    elif method == "prioritized":
        result = best_prioritized(warehouse, assignment, horizon)
    else:
        result = conflict_based_search(warehouse, assignment, horizon, time_limit=time_limit)

    if result is not None:
        result.assignment = assignment
        result.elapsed = time.time() - start
    return result
