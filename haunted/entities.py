"""The janitor, the ghosts, the cabinets they live in, and the mess on the floor."""
from .constants import BATTERY_MAX, SCRUBS_PER_SPILL, SCRUBS_PER_ECTO


class Machine:
    """An arcade cabinet. One row tall, one or more cells wide."""

    def __init__(self, cells, name, phase):
        self.cells = cells          # list of (x, y)
        self.name = name
        self.phase = phase          # offsets the idle screen flicker
        self.charge = 0             # ticks of warning flicker left before a ghost comes out
        self.exit = None            # the floor cell the ghost will appear on
        self.spawns = []            # floor cells touching this cabinet


class Ghost:
    def __init__(self, x, y, home):
        self.x = x
        self.y = y
        self.home = home            # the Machine it came out of
        self.scared = 0             # ticks left of fleeing
        self.move_t = 0
        self.dir = (0, 1)
        self.age = 0


class Spill:
    def __init__(self, x, y, kind="spill"):
        self.x = x
        self.y = y
        self.kind = kind            # "spill" (slushie) or "ecto" (ghost goo)
        self.hp = SCRUBS_PER_SPILL if kind == "spill" else SCRUBS_PER_ECTO
        self.max_hp = self.hp


class Janitor:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.facing = (0, -1)
        self.light = False
        self.battery = BATTERY_MAX
        self.move_t = 0
        self.scrub_t = 0
        self.invuln = 0
        self.want = None            # direction requested this tick
        self.want_t = 0
