"""The arcade floor plan: walls, the front door, the cabinets and where ghosts climb out."""
from .constants import FIELD_W, FIELD_H, MACHINE_NAMES
from .entities import Machine

# Legend:  #  wall     M  cabinet     D  front door     .  carpet
MAP = (
    "################################",
    "#..............................#",
    "#.MM.MM.MM.MM......MM.MM.MM.MM.#",
    "#..............................#",
    "#..............................#",
    "#....MMMM.....MMMM.....MMMM....#",
    "#..............................#",
    "#..............................#",
    "#..............................#",
    "#..............................#",
    "#....MMMM.....MMMM.....MMMM....#",
    "#..............................#",
    "#..............................#",
    "#.MM.MM.MM.MM......MM.MM.MM.MM.#",
    "#..............................#",
    "###############DD###############",
)

assert len(MAP) == FIELD_H and all(len(row) == FIELD_W for row in MAP), "map must be %dx%d" % (FIELD_W, FIELD_H)

DIRS = ((0, -1), (0, 1), (-1, 0), (1, 0))      # up, down, left, right


class World:
    def __init__(self, rng):
        self.walls = set()
        self.doors = set()
        self.floor = set()
        self.machines = []
        self.machine_at = {}
        names = list(MACHINE_NAMES)
        for y, row in enumerate(MAP):
            x = 0
            while x < FIELD_W:
                ch = row[x]
                if ch == "#":
                    self.walls.add((x, y))
                elif ch == "D":
                    self.doors.add((x, y))
                elif ch == ".":
                    self.floor.add((x, y))
                elif ch == "M":
                    # a run of M on one row is a single cabinet
                    cells = []
                    while x < FIELD_W and row[x] == "M":
                        cells.append((x, y))
                        x += 1
                    name = names.pop(0) if names else "CABINET %d" % (len(self.machines) + 1)
                    m = Machine(cells, name, rng.random() * 6.28)
                    self.machines.append(m)
                    for c in cells:
                        self.machine_at[c] = m
                    continue
                x += 1
        for m in self.machines:
            seen = set()
            for cx, cy in m.cells:
                for dx, dy in DIRS:
                    c = (cx + dx, cy + dy)
                    if c in self.floor and c not in seen:
                        seen.add(c)
                        m.spawns.append(c)
        # the janitor clocks in just inside the front door
        self.start = (FIELD_W // 2 - 1, FIELD_H - 2)

    # ------------------------------------------------------------ queries
    def passable(self, x, y):
        return (x, y) in self.floor

    def machine_near(self, x, y):
        """The cabinet touching this cell, if any."""
        for dx, dy in DIRS:
            m = self.machine_at.get((x + dx, y + dy))
            if m is not None:
                return m
        return None

    def near_machine(self, x, y):
        return self.machine_near(x, y) is not None

    def random_floor(self, rng, count, exclude, min_start_dist=4):
        """Pick `count` distinct floor cells away from the door and not in `exclude`."""
        sx, sy = self.start
        pool = [c for c in self.floor
                if c not in exclude and abs(c[0] - sx) + abs(c[1] - sy) >= min_start_dist]
        rng.shuffle(pool)
        return pool[:count]
