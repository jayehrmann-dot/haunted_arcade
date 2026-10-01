"""Game loop, input, the janitor, the flashlight, ghost AI, levels and scoring."""
import curses
import json
import os
import random
import time
from collections import deque

from .constants import (
    FPS, TICK, START_LIVES, EXTRA_LIFE_EVERY, MOVE_COOLDOWN, SCRUB_COOLDOWN,
    BEAM_LENGTH, BATTERY_MAX, BATTERY_DRAIN, BATTERY_CHARGE, BATTERY_MIN_ON,
    SCARE_TICKS, CHARGE_TICKS, DEATH_TICKS, INVULN_TICKS, BANNER_TICKS,
    ECTO_CHANCE, ECTO_EXTRA_CAP, SCORE, level_params,
    LINES_START, LINES_LEVEL, LINES_STIR, LINES_BANISH, LINES_SPILL, LINES_ECTO,
    LINES_ECTO_DROP, LINES_BUSY, LINES_DEAD_BATTERY, LINES_HIT, LINES_IDLE, LINES_EXTRA,
)
from .world import World, DIRS
from .entities import Janitor, Ghost, Spill

HIGH_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "highscore.json")

KEYS_UP = (curses.KEY_UP, ord("w"), ord("W"))
KEYS_DOWN = (curses.KEY_DOWN, ord("s"), ord("S"))
KEYS_LEFT = (curses.KEY_LEFT, ord("a"), ord("A"))
KEYS_RIGHT = (curses.KEY_RIGHT, ord("d"), ord("D"))
KEYS_MOP = (ord(" "), ord("m"), ord("M"))
KEYS_LIGHT = (ord("f"), ord("F"))
ESC = 27


class Game:
    def __init__(self, stdscr, renderer=None):
        self.stdscr = stdscr
        if renderer is None:
            from .render import Renderer
            renderer = Renderer(stdscr)
        self.r = renderer
        self.rng = random.Random()
        self.world = World(self.rng)
        self.high = self.load_high()
        self.running = True
        self.mode = "title"
        self.prev_mode = "title"
        self.tick = 0
        self.title_t = 0
        self.messages = deque(maxlen=2)
        self.msg_expire = 0
        self.reset_state()

    # ------------------------------------------------------------ setup
    def reset_state(self):
        self.score = 0
        self.lives = START_LIVES
        self.level = 0
        self.next_life = EXTRA_LIFE_EVERY
        self.params = level_params(1)
        self.jan = Janitor(*self.world.start)
        self.ghosts = []
        self.trash = set()
        self.spills = {}
        self.beam = set()
        self.banner = ""
        self.banner_t = 0
        self.dead_t = 0
        self.spawn_t = 0
        self.busy_t = 0
        self.ecto_msg_t = 0
        self.idle_t = FPS * 10
        self.banished = 0
        self.clear_charges()
        self.messages.clear()

    def clear_charges(self):
        for m in self.world.machines:
            m.charge = 0
            m.exit = None

    def load_high(self):
        try:
            with open(HIGH_PATH) as f:
                return int(json.load(f).get("high", 0))
        except (OSError, ValueError):
            return 0

    def save_high(self):
        if self.score > self.high:
            self.high = self.score
        try:
            with open(HIGH_PATH, "w") as f:
                json.dump({"high": self.high}, f)
        except OSError:
            pass

    # ------------------------------------------------------------ messages
    def say(self, text, kind="msg", secs=5):
        self.messages.append((text, kind))
        self.msg_expire = self.tick + int(secs * FPS)
        self.idle_t = FPS * 14

    def log(self, lines, kind="msg", secs=5, **kw):
        if "name" not in kw:
            kw["name"] = self.rng.choice(self.world.machines).name
        self.say(self.rng.choice(lines).format(**kw), kind, secs)

    # ------------------------------------------------------------ main loop
    def run(self):
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        next_t = time.time()
        while self.running:
            self.handle_input()
            self.step()
            self.r.draw(self)
            next_t += TICK
            delay = next_t - time.time()
            if delay > 0:
                time.sleep(delay)
            else:
                next_t = time.time()

    def step(self):
        """One simulation tick (also used headless by the tests)."""
        self.tick += 1
        if self.mode == "title":
            self.title_t += 1
        elif self.mode in ("play", "dead", "clear"):
            self.update()
        if self.messages and self.tick > self.msg_expire:
            self.messages.clear()

    def handle_input(self):
        while True:
            k = self.stdscr.getch()
            if k == -1:
                break
            if k == curses.KEY_RESIZE:
                continue
            getattr(self, "keys_" + self.mode)(k)

    # ------------------------------------------------------------ key handlers
    def keys_title(self, k):
        if k in (ord("n"), ord("N"), 10, 13, ord(" ")):
            self.start_new()
        elif k == ord("?"):
            self.prev_mode = "title"
            self.mode = "help"
        elif k in (ord("q"), ord("Q"), ESC):
            self.running = False

    def keys_help(self, k):
        if k != -1:
            self.mode = self.prev_mode

    def keys_pause(self, k):
        if k in (ord("p"), ord("P"), ESC, ord(" ")):
            self.mode = "play"
        elif k in (ord("q"), ord("Q")):
            self.mode = "quit"
        elif k == ord("?"):
            self.prev_mode = "pause"
            self.mode = "help"

    def keys_quit(self, k):
        if k in (ord("y"), ord("Y")):
            self.save_high()
            self.running = False
        elif k != -1:
            self.mode = "play"

    def keys_gameover(self, k):
        if k in (ord("n"), ord("N"), 10, 13, ord(" ")):
            self.start_new()
        elif k in (ord("q"), ord("Q"), ESC):
            self.running = False

    def keys_dead(self, k):
        if k in (ord("q"), ord("Q"), ESC):
            self.mode = "quit"

    def keys_clear(self, k):
        if k in (ord("p"), ord("P")):
            self.mode = "pause"
        elif k == ord("?"):
            self.prev_mode = "play"
            self.mode = "help"
        elif k in (ord("q"), ord("Q"), ESC):
            self.mode = "quit"

    def keys_play(self, k):
        j = self.jan
        d = None
        if k in KEYS_UP:
            d = (0, -1)
        elif k in KEYS_DOWN:
            d = (0, 1)
        elif k in KEYS_LEFT:
            d = (-1, 0)
        elif k in KEYS_RIGHT:
            d = (1, 0)
        if d is not None:
            j.facing = d
            j.want = d
            j.want_t = MOVE_COOLDOWN + 1
        elif k in KEYS_MOP:
            self.mop()
        elif k in KEYS_LIGHT:
            self.toggle_light()
        elif k in (ord("p"), ord("P")):
            self.mode = "pause"
        elif k == ord("?"):
            self.prev_mode = "play"
            self.mode = "help"
        elif k in (ord("q"), ord("Q"), ESC):
            self.mode = "quit"

    # ------------------------------------------------------------ game flow
    def start_new(self):
        self.reset_state()
        self.mode = "play"
        self.start_level(1)
        self.log(LINES_START, "msg_good", 6)

    def start_level(self, n):
        self.level = n
        self.params = level_params(n)
        self.ghosts = []
        self.clear_charges()
        self.jan = Janitor(*self.world.start)
        self.beam = set()
        p = self.params
        taken = set()
        self.trash = set(self.world.random_floor(self.rng, p["trash"], taken))
        taken |= self.trash
        self.spills = {}
        for c in self.world.random_floor(self.rng, p["spills"], taken):
            self.spills[c] = Spill(c[0], c[1], "spill")
        self.spawn_t = BANNER_TICKS + 30
        self.banner = "LEVEL %d" % n
        self.banner_t = BANNER_TICKS
        self.mode = "play"
        if n > 1:
            self.log(LINES_LEVEL, "msg_good", 5)

    def level_cleared(self):
        bonus = SCORE["level"] * self.level
        self.add_score(bonus)
        self.banner = "LEVEL %d CLEAR" % self.level
        self.banner_t = BANNER_TICKS
        self.mode = "clear"
        self.ghosts = []
        self.clear_charges()
        self.jan.light = False
        self.beam = set()
        self.say("Spotless. Bonus %d." % bonus, "msg_good", 4)

    def add_score(self, n):
        self.score += n
        if self.score >= self.next_life:
            self.next_life += EXTRA_LIFE_EVERY
            self.lives += 1
            self.log(LINES_EXTRA, "msg_good")

    def game_over(self):
        self.mode = "gameover"
        self.banner = "GAME OVER"
        self.save_high()

    # ------------------------------------------------------------ janitor actions
    def toggle_light(self):
        j = self.jan
        if self.mode != "play":
            return
        if j.light:
            j.light = False
        elif j.battery >= BATTERY_MIN_ON:
            j.light = True
        else:
            self.log(LINES_DEAD_BATTERY, "msg_alert", 2)

    def busy(self):
        """The player tried to clean with the flashlight on."""
        if self.busy_t <= 0:
            self.busy_t = FPS * 2
            self.log(LINES_BUSY, "msg_alert", 2)

    def mop(self):
        j = self.jan
        if self.mode != "play" or j.scrub_t > 0:
            return
        j.scrub_t = SCRUB_COOLDOWN
        if j.light:
            self.busy()
            return
        sp = self.spills.get((j.x, j.y))
        if sp is None:
            return
        sp.hp -= 1
        if sp.hp <= 0:
            del self.spills[(j.x, j.y)]
            self.add_score(SCORE[sp.kind])
            self.log(LINES_ECTO if sp.kind == "ecto" else LINES_SPILL, "msg_good", 3)

    def kill_janitor(self):
        self.mode = "dead"
        self.dead_t = DEATH_TICKS
        self.jan.light = False
        self.jan.want = None
        self.beam = set()
        self.r.flash()
        try:
            curses.beep()
        except curses.error:
            pass
        self.log(LINES_HIT, "msg_alert", 4)

    def respawn(self):
        self.lives -= 1
        if self.lives < 0:
            self.game_over()
            return
        battery = self.jan.battery
        self.jan = Janitor(*self.world.start)
        self.jan.battery = max(battery, BATTERY_MIN_ON)
        self.jan.invuln = INVULN_TICKS
        self.ghosts = []
        self.clear_charges()
        self.spawn_t = 60
        self.mode = "play"

    # ------------------------------------------------------------ update
    def update(self):
        if self.banner_t > 0:
            self.banner_t -= 1
        if self.busy_t > 0:
            self.busy_t -= 1
        if self.ecto_msg_t > 0:
            self.ecto_msg_t -= 1
        if self.mode == "clear":
            if self.banner_t <= 0:
                self.start_level(self.level + 1)
            return
        if self.mode == "dead":
            self.dead_t -= 1
            if self.dead_t <= 0:
                self.respawn()
            return
        self.update_janitor()
        self.update_battery()
        self.beam = self.compute_beam()
        self.check_hit()
        if self.mode != "play":
            return
        self.update_spawns()
        self.update_ghosts()
        self.check_hit()
        if self.mode != "play":
            return
        self.check_level_end()
        self.idle_chatter()

    def update_janitor(self):
        j = self.jan
        if j.move_t > 0:
            j.move_t -= 1
        if j.scrub_t > 0:
            j.scrub_t -= 1
        if j.invuln > 0:
            j.invuln -= 1
        if j.want is not None:
            if j.move_t <= 0:
                nx, ny = j.x + j.want[0], j.y + j.want[1]
                if self.world.passable(nx, ny):
                    j.x, j.y = nx, ny
                    j.move_t = MOVE_COOLDOWN
                j.want = None
            else:
                j.want_t -= 1
                if j.want_t <= 0:
                    j.want = None
        pos = (j.x, j.y)
        if pos in self.trash:
            if j.light:
                self.busy()
            else:
                self.trash.discard(pos)
                self.add_score(SCORE["trash"])

    def update_battery(self):
        j = self.jan
        if j.light:
            j.battery -= BATTERY_DRAIN
            if j.battery <= 0:
                j.battery = 0.0
                j.light = False
                self.say("Flashlight died. Recharging.", "msg_alert", 2)
        else:
            j.battery = min(BATTERY_MAX, j.battery + BATTERY_CHARGE)

    def compute_beam(self):
        """Cells lit by the flashlight: a cone that widens with distance and stops at walls."""
        j = self.jan
        if not j.light:
            return set()
        dx, dy = j.facing
        cells = set()
        for d in range(1, BEAM_LENGTH + 1):
            cx, cy = j.x + dx * d, j.y + dy * d
            if not self.world.passable(cx, cy):
                break
            spread = 0 if d <= 2 else (1 if d <= 4 else 2)
            for s in range(-spread, spread + 1):
                c = (cx + dy * s, cy + dx * s)
                if self.world.passable(*c):
                    cells.add(c)
        return cells

    # ------------------------------------------------------------ ghosts
    def update_spawns(self):
        if self.banner_t > 0:
            return
        charging = 0
        for m in self.world.machines:
            if m.charge > 0:
                m.charge -= 1
                if m.charge == 0 and m.exit is not None:
                    g = Ghost(m.exit[0], m.exit[1], m)
                    g.move_t = self.params["period"]
                    self.ghosts.append(g)
                    m.exit = None
                else:
                    charging += 1
        self.spawn_t -= 1
        if self.spawn_t > 0 or len(self.ghosts) + charging >= self.params["max_ghosts"]:
            return
        self.spawn_t = self.params["spawn_ticks"]
        jx, jy = self.jan.x, self.jan.y
        candidates = [m for m in self.world.machines
                      if m.charge == 0 and m.spawns
                      and min(abs(x - jx) + abs(y - jy) for x, y in m.spawns) >= 5]
        if not candidates:
            return
        m = self.rng.choice(candidates)
        m.charge = CHARGE_TICKS
        m.exit = self.rng.choice(m.spawns)
        self.log(LINES_STIR, "msg", 4, name=m.name)

    def update_ghosts(self):
        p = self.params
        for g in list(self.ghosts):
            g.age += 1
            if (g.x, g.y) in self.beam:
                g.scared = SCARE_TICKS
            if g.scared > 0:
                g.scared -= 1
                if self.world.near_machine(g.x, g.y):
                    self.banish(g)
                    continue
            g.move_t -= 1
            if g.move_t <= 0:
                g.move_t = max(3, p["period"] - 2) if g.scared else p["period"]
                self.ghost_step(g)
                if g.scared and self.world.near_machine(g.x, g.y):
                    self.banish(g)
                    continue
            if not g.scared and self.rng.random() < ECTO_CHANCE:
                self.drop_ecto(g.x, g.y)

    def ghost_step(self, g):
        opts = [(g.x + dx, g.y + dy, (dx, dy)) for dx, dy in DIRS
                if self.world.passable(g.x + dx, g.y + dy)]
        if not opts:
            return
        jx, jy = self.jan.x, self.jan.y

        def dist(o):
            return abs(o[0] - jx) + abs(o[1] - jy)

        if g.scared:
            best = max(dist(o) for o in opts)
            pick = self.rng.choice([o for o in opts if dist(o) == best])
        elif self.rng.random() < 0.3:
            back = (-g.dir[0], -g.dir[1])
            forward = [o for o in opts if o[2] != back] or opts
            pick = self.rng.choice(forward)
        else:
            best = min(dist(o) for o in opts)
            pick = self.rng.choice([o for o in opts if dist(o) == best])
        g.x, g.y, g.dir = pick

    def banish(self, g):
        if g in self.ghosts:
            self.ghosts.remove(g)
        self.banished += 1
        self.add_score(SCORE["banish"])
        m = self.world.machine_near(g.x, g.y) or g.home
        self.log(LINES_BANISH, "msg_good", 3, name=m.name)

    def drop_ecto(self, x, y):
        pos = (x, y)
        if pos in self.trash or pos in self.spills or pos == (self.jan.x, self.jan.y):
            return
        if len(self.spills) >= self.params["spills"] + ECTO_EXTRA_CAP:
            return
        self.spills[pos] = Spill(x, y, "ecto")
        if self.ecto_msg_t <= 0:
            self.ecto_msg_t = FPS * 6
            self.log(LINES_ECTO_DROP, "msg_alert", 3)

    def check_hit(self):
        if self.mode != "play" or self.jan.invuln > 0:
            return
        pos = (self.jan.x, self.jan.y)
        for g in self.ghosts:
            if not g.scared and (g.x, g.y) == pos:
                self.kill_janitor()
                return

    # ------------------------------------------------------------ levels
    def check_level_end(self):
        if self.mode == "play" and self.banner_t <= 0 and not self.trash and not self.spills:
            self.level_cleared()

    def idle_chatter(self):
        self.idle_t -= 1
        if self.idle_t <= 0 and not self.messages:
            self.idle_t = FPS * 14
            self.log(LINES_IDLE, "msg", 5)
