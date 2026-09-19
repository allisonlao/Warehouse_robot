DIRECTIONS = {
    "North": (0, -1),
    "South": (0, 1),
    "East": (1, 0),
    "West": (-1, 0),
}


class Warehouse:
    def __init__(self, lines):
        self.grid = [list(line) for line in lines]
        self.height = len(self.grid)
        self.width = len(self.grid[0])
        self.starts = []
        self.items = []
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                if cell == "S":
                    self.starts.append((x, y))
                    self.grid[y][x] = "."
                elif cell == "P":
                    self.items.append((x, y))
                    self.grid[y][x] = "."
        self.start = self.starts[0]

    def in_bounds(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def is_passable(self, pos):
        return self.in_bounds(pos) and self.grid[pos[1]][pos[0]] != "#"

    def cell_cost(self, pos):
        return 3 if self.grid[pos[1]][pos[0]] == "c" else 1

    def render(self, path=None):
        return self.render_fleet([path or []])

    def render_fleet(self, paths):
        canvas = [row[:] for row in self.grid]
        for index, path in enumerate(paths):
            mark = "*" if len(paths) == 1 else str(index)
            for x, y in path:
                if canvas[y][x] in ".c":
                    canvas[y][x] = mark
        for x, y in self.items:
            canvas[y][x] = "P"
        for x, y in self.starts:
            canvas[y][x] = "S"
        return "\n".join("".join(row) for row in canvas)
