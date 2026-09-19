import heapq
from itertools import count

from heuristics import combined_heuristic
from warehouse import DIRECTIONS


class Constraints:
    def __init__(self, vertex=None, edge=None):
        self.vertex = set(vertex or ())
        self.edge = set(edge or ())

    def copy(self):
        return Constraints(self.vertex, self.edge)

    def add_vertex(self, pos, time):
        self.vertex.add((pos, time))

    def add_edge(self, source, target, time):
        self.edge.add((source, target, time))

    def last_blocked(self):
        latest = {}
        for pos, time in self.vertex:
            latest[pos] = max(latest.get(pos, -1), time)
        return latest


class SpaceTimePlan:
    def __init__(self, path, cost, expanded):
        self.path = path
        self.cost = cost
        self.expanded = expanded


def build_path(parent, state):
    path = []
    while state is not None:
        path.append(state[0])
        state = parent[state]
    path.reverse()
    return path


def plan_robot(warehouse, start, items, constraints, horizon=150):
    if (start, 0) in constraints.vertex:
        return None

    last_blocked = constraints.last_blocked()
    begin = (start, frozenset(items) - {start}, 0)
    tie_breaker = count()
    frontier = [(combined_heuristic(begin, None), next(tie_breaker), 0, begin)]
    best_cost = {begin: 0}
    parent = {begin: None}
    expanded = 0

    while frontier:
        _, _, cost, state = heapq.heappop(frontier)

        if cost > best_cost[state]:
            continue

        pos, remaining, time = state

        if not remaining and time > last_blocked.get(pos, -1):
            return SpaceTimePlan(build_path(parent, state), cost, expanded)

        expanded += 1

        if time >= horizon:
            continue

        moves = [(pos, 1)]
        for dx, dy in DIRECTIONS.values():
            neighbor = (pos[0] + dx, pos[1] + dy)
            if warehouse.is_passable(neighbor):
                moves.append((neighbor, warehouse.cell_cost(neighbor)))

        for next_pos, step_cost in moves:
            if (next_pos, time + 1) in constraints.vertex:
                continue
            if (pos, next_pos, time + 1) in constraints.edge:
                continue

            child = (next_pos, remaining - {next_pos}, time + 1)
            new_cost = cost + step_cost

            if new_cost < best_cost.get(child, float("inf")):
                best_cost[child] = new_cost
                parent[child] = state
                priority = new_cost + combined_heuristic(child, None)
                heapq.heappush(frontier, (priority, next(tie_breaker), new_cost, child))

    return None
