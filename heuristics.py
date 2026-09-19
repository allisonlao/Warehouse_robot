def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def null_heuristic(state, problem=None):
    return 0


def furthest_item(state, problem):
    position, remaining = state[0], state[1]
    if not remaining:
        return 0
    return max(manhattan(position, item) for item in remaining)


def span_heuristic(state, problem):
    position, remaining = state[0], state[1]
    if not remaining:
        return 0
    items = list(remaining)
    span = 0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            span = max(span, manhattan(items[i], items[j]))
    nearest = min(manhattan(position, item) for item in items)
    return nearest + span


def combined_heuristic(state, problem):
    return max(furthest_item(state, problem), span_heuristic(state, problem))
