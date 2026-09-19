import random

from warehouse import Warehouse


def generate_warehouse(width, height, num_items, seed=0, congestion=0.1, num_robots=1, cross_aisle=6):
    rng = random.Random(seed)
    grid = [["#"] * width for _ in range(height)]

    for y in range(height):
        for x in range(width):
            if y % 3 == 0 or x % cross_aisle == 0:
                grid[y][x] = "c" if rng.random() < congestion else "."

    dock_rows = list(range(0, height, 3))
    if num_robots > len(dock_rows):
        raise ValueError("layout only has room for %d robots" % len(dock_rows))

    for y in dock_rows:
        grid[y][0] = "."
    for y in dock_rows[:num_robots]:
        grid[y][0] = "S"

    open_cells = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if grid[y][x] != "#" and not (x == 0 and y % 3 == 0)
    ]
    for x, y in rng.sample(open_cells, num_items):
        grid[y][x] = "P"

    return Warehouse(["".join(row) for row in grid])
