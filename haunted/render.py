"""Curses renderer: block-digit HUD, the arcade floor, sprites, beam and overlays."""
import curses
import math

from .constants import (
    VIEW_COLS, VIEW_ROWS, HUD_ROWS, FIELD_ROWS, FIELD_TOP, MSG_TOP,
    FIELD_W, FIELD_H, CELL_W, BATTERY_MAX, BATTERY_MIN_ON, SCARE_TICKS, PALETTE, FONT,
    PLAYER, GHOST_FRAMES, CABINET, WALL, TRASH, SPILL, ECTO, BEAM, LIFE_ICON,
)

CONTROLS = [
    "ARROWS / WASD ...... walk (you face the way you last moved)",
    "SPACE or M ......... mop the puddle you're standing on",
    "F .................. flashlight on / off",
    "P .................. pause          ? ...... this card",
    "Q or ESC ........... quit (asks first)",
    "",
    "Walk over TRASH to pick it up. Stand on a SPILL and mop it:",
    "slushies take three strokes, ectoplasm two. Clear every bit",
    "of mess and the next shift starts, with more ghosts.",
    "",
    "Ghosts climb out of cabinets that flicker red. They chase",
    "you. One touch and you drop the mop. Shine the FLASHLIGHT",
    "on a ghost and it flees; if it flees next to any cabinet it",
    "gets pulled back inside for 50 points.",
    "",
    "You cannot pick up or mop anything while the light is on,",
    "and the battery only lasts a few seconds. Light. Scatter.",
    "Switch off. Clean. Repeat.",
]


class Renderer:
    def __init__(self, stdscr):
        self.scr = stdscr
        self.pairs = {}
        self.colors_ok = curses.has_colors()
        if self.colors_ok:
            curses.start_color()
            try:
                curses.use_default_colors()
            except curses.error:
                pass
        self.many = self.colors_ok and curses.COLORS >= 256
        self.max_pairs = curses.COLOR_PAIRS if self.colors_ok else 0
        self.oy = self.ox = 0
        self.flash_t = 0

    # ------------------------------------------------------------ colours
    def cidx(self, name):
        full, basic = PALETTE[name]
        return full if self.many else basic

    def attr(self, fg, bg, bold=False):
        if not self.colors_ok:
            return curses.A_BOLD if bold else 0
        key = (self.cidx(fg), self.cidx(bg))
        if key not in self.pairs:
            n = len(self.pairs) + 1
            if n >= self.max_pairs:
                return 0
            try:
                curses.init_pair(n, key[0], key[1])
            except curses.error:
                return 0
            self.pairs[key] = n
        a = curses.color_pair(self.pairs[key])
        return a | curses.A_BOLD if bold else a

    def flash(self):
        self.flash_t = 2

    def put(self, y, x, s, attr=0):
        try:
            self.scr.addstr(y, x, s, attr)
        except curses.error:
            pass

    def fill(self, y0, x0, rows, cols, attr):
        for y in range(y0, y0 + rows):
            self.put(y, x0, " " * cols, attr)

    def center(self, y, text, attr=0):
        self.put(y, self.ox + (VIEW_COLS - len(text)) // 2, text, attr)

    def big(self, y, x, text, attr):
        for i, ch in enumerate(text.upper()):
            glyph = FONT.get(ch, FONT[" "])
            for r, row in enumerate(glyph):
                for c, px in enumerate(row):
                    if px == "█":
                        self.put(y + r, x + i * 4 + c, "█", attr)

    def big_center(self, y, text, attr):
        w = len(text) * 4 - 1
        self.big(y, self.ox + (VIEW_COLS - w) // 2, text, attr)

    def cell(self, cx, cy, s, attr):
        """Draw one playfield cell (two columns)."""
        self.put(self.oy + FIELD_TOP + cy, self.ox + cx * CELL_W, s, attr)

    # ------------------------------------------------------------ frame
    def draw(self, g):
        self.scr.erase()
        rows, cols = self.scr.getmaxyx()
        if rows < VIEW_ROWS or cols < VIEW_COLS:
            self.put(0, 0, "Haunted Arcade needs a terminal of at least %dx%d (you have %dx%d)."
                     % (VIEW_COLS, VIEW_ROWS, cols, rows))
            self.put(1, 0, "Enlarge the window.")
            self.scr.refresh()
            return
        self.oy = (rows - VIEW_ROWS) // 2
        self.ox = (cols - VIEW_COLS) // 2
        if g.mode == "title" or (g.mode == "help" and g.prev_mode == "title"):
            self.draw_title(g)
        else:
            self.draw_hud(g)
            self.draw_field(g)
            self.draw_messages(g)
        if g.mode == "help":
            self.draw_help()
        elif g.mode == "pause":
            self.overlay(["PAUSED", "", "P to resume   Q to quit   ? for the card"])
        elif g.mode == "quit":
            self.overlay(["CLOCK OUT EARLY?", "", "Y to quit, any other key to keep mopping"])
        elif g.mode == "gameover":
            self.draw_gameover(g)
        if g.banner_t > 0 and g.mode in ("play", "clear") and g.banner:
            self.draw_banner(g)
        if self.flash_t > 0:
            self.flash_t -= 1
            self.fill(self.oy + FIELD_TOP, self.ox, FIELD_ROWS, VIEW_COLS, self.attr("hud", "hud"))
        self.scr.refresh()

    # ------------------------------------------------------------ HUD
    def draw_hud(self, g):
        y = self.oy
        self.fill(y, self.ox, HUD_ROWS, VIEW_COLS, self.attr("hud", "hud_bg"))
        self.big(y, self.ox, "%06d" % g.score, self.attr("player", "hud_bg", True))
        x = self.ox + 26
        self.put(y, x, "LEVEL", self.attr("hud_dim", "hud_bg"))
        self.put(y, x + 6, "%02d" % g.level, self.attr("hud", "hud_bg", True))
        self.put(y + 1, x, "LIVES", self.attr("hud_dim", "hud_bg"))
        self.put(y + 1, x + 6, " ".join([LIFE_ICON] * max(0, g.lives)).ljust(12), self.attr("player", "hud_bg", True))
        self.put(y + 2, x, "LIGHT", self.attr("hud_dim", "hud_bg"))
        j = g.jan
        segs = int(round(j.battery * 10 / BATTERY_MAX))
        if j.light:
            bar_fg = "beam2"
        elif j.battery < BATTERY_MIN_ON:
            bar_fg = "hud_red"
        else:
            bar_fg = "hud_dim"
        self.put(y + 2, x + 6, "█" * segs, self.attr(bar_fg, "hud_bg", j.light))
        self.put(y + 2, x + 6 + segs, "·" * (10 - segs), self.attr("hud_dim", "hud_bg"))
        self.put(y + 2, x + 17, "ON " if j.light else "OFF", self.attr("beam2" if j.light else "hud_dim", "hud_bg", j.light))
        self.put(y + 4, x, "HAUNTED ARCADE  NIGHT SHIFT", self.attr("hud_dim", "hud_bg"))
        x = self.ox + 50
        self.put(y, x, "HI", self.attr("hud_dim", "hud_bg"))
        self.put(y, x + 7, "%06d" % max(g.high, g.score), self.attr("hud_gold", "hud_bg"))
        self.put(y + 1, x, "TRASH", self.attr("hud_dim", "hud_bg"))
        self.put(y + 1, x + 11, "%2d" % len(g.trash), self.attr("trash2", "hud_bg", True))
        self.put(y + 2, x, "SPILLS", self.attr("hud_dim", "hud_bg"))
        self.put(y + 2, x + 11, "%2d" % len(g.spills), self.attr("spill3", "hud_bg", True))
        self.put(y + 3, x, "GHOSTS", self.attr("hud_dim", "hud_bg"))
        self.put(y + 3, x + 11, "%2d" % len(g.ghosts), self.attr("ghost", "hud_bg", True))

    # ------------------------------------------------------------ the floor
    def draw_field(self, g):
        w = g.world
        t = g.tick
        clear_blink = g.mode == "clear" and (t // 6) % 2 == 0
        for cy in range(FIELD_H):
            for cx in range(FIELD_W):
                pos = (cx, cy)
                if pos in w.walls:
                    self.cell(cx, cy, WALL, self.attr("wall", "hud_bg"))
                elif pos in w.doors:
                    self.cell(cx, cy, WALL, self.attr("door2" if clear_blink else "door", "hud_bg", clear_blink))
                elif pos in w.machine_at:
                    m = w.machine_at[pos]
                    if m.charge > 0:
                        fg = "cab_hot" if (t // 3) % 2 else "cab_hot2"
                        bold = True
                    else:
                        fg = "cab" if math.sin(t / 9.0 + m.phase) > 0.3 else "cab2"
                        bold = False
                    self.cell(cx, cy, CABINET, self.attr(fg, "hud_bg", bold))
                else:
                    bg = "floor" if (cx + cy) % 2 else "floor2"
                    if pos in g.beam:
                        self.cell(cx, cy, BEAM, self.attr("beam" if (cx + t // 2) % 2 else "beam2", bg))
                    else:
                        self.cell(cx, cy, "  ", self.attr(bg, bg))
        # mess
        for cx, cy in g.trash:
            bg = "floor" if (cx + cy) % 2 else "floor2"
            self.cell(cx, cy, TRASH, self.attr("trash2" if (cx, cy) in g.beam else "trash", bg, True))
        for (cx, cy), sp in g.spills.items():
            bg = "floor" if (cx + cy) % 2 else "floor2"
            if sp.kind == "ecto":
                ch = ECTO[min(sp.hp, len(ECTO)) - 1]
                fg = "ecto2" if (t // 5) % 2 else "ecto"
            else:
                ch = SPILL[min(sp.hp, len(SPILL)) - 1]
                fg = ("spill", "spill2", "spill3")[min(sp.hp, 3) - 1]
            self.cell(cx, cy, ch, self.attr(fg, bg, True))
        # ghosts
        for gh in g.ghosts:
            bg = "floor" if (gh.x + gh.y) % 2 else "floor2"
            ch = GHOST_FRAMES[((t // 4) + gh.age) % len(GHOST_FRAMES)]
            if gh.scared:
                ending = gh.scared < SCARE_TICKS // 3
                fg = "scared2" if (ending and (t // 3) % 2) else "scared"
            else:
                fg = "ghost" if (t // 8 + gh.age) % 5 else "ghost_dim"
            self.cell(gh.x, gh.y, ch, self.attr(fg, bg, True))
        # the janitor
        if g.mode == "dead":
            if (t // 3) % 2:
                self.cell(g.jan.x, g.jan.y, PLAYER, self.attr("hud_red", "hud_bg", True))
            return
        j = g.jan
        if j.invuln > 0 and (t // 3) % 2 == 0:
            return
        bg = "floor" if (j.x + j.y) % 2 else "floor2"
        self.cell(j.x, j.y, PLAYER, self.attr("player_lit" if j.light else "player", bg, True))

    # ------------------------------------------------------------ messages
    def draw_messages(self, g):
        y = self.oy + MSG_TOP
        self.fill(y, self.ox, 2, VIEW_COLS, self.attr("hud", "hud_bg"))
        if g.messages:
            text, kind = g.messages[-1]
            self.put(y, self.ox + 1, text[:VIEW_COLS - 2], self.attr(kind, "hud_bg", kind != "msg"))
        self.center(y + 1, "ARROWS MOVE   SPACE MOP   F LIGHT   P PAUSE   ? HELP   Q QUIT",
                    self.attr("hud_dim", "hud_bg"))

    # ------------------------------------------------------------ overlays
    def draw_banner(self, g):
        y = self.oy + FIELD_TOP + 4
        text = g.banner
        w = len(text) * 4 + 3
        x = self.ox + (VIEW_COLS - w) // 2
        self.fill(y - 1, x, 7, w, self.attr("panel_fg", "panel"))
        fg = "title3" if "CLEAR" in text else "title2"
        self.big(y, x + 2, text, self.attr(fg, "panel", True))

    def overlay(self, lines):
        w = max(len(l) for l in lines) + 6
        h = len(lines) + 2
        y = self.oy + FIELD_TOP + (FIELD_ROWS - h) // 2
        x = self.ox + (VIEW_COLS - w) // 2
        self.fill(y, x, h, w, self.attr("panel_fg", "panel"))
        for i, l in enumerate(lines):
            self.put(y + 1 + i, x + (w - len(l)) // 2, l, self.attr("title2" if i == 0 else "panel_fg", "panel", i == 0))

    def draw_help(self):
        self.fill(self.oy, self.ox, VIEW_ROWS, VIEW_COLS, self.attr("panel_fg", "panel"))
        self.center(self.oy + 1, "NIGHT SHIFT CARD", self.attr("title2", "panel", True))
        for i, line in enumerate(CONTROLS):
            self.put(self.oy + 3 + i, self.ox + 2, line, self.attr("panel_fg", "panel"))
        self.center(self.oy + VIEW_ROWS - 2, "any key to return", self.attr("hud_dim", "panel"))

    def draw_gameover(self, g):
        y = self.oy + FIELD_TOP + 2
        self.fill(y - 1, self.ox + 4, 13, VIEW_COLS - 8, self.attr("panel_fg", "panel"))
        self.big_center(y, g.banner, self.attr("hud_red", "panel", True))
        self.center(y + 6, "FINAL SCORE %06d     LEVEL %d" % (g.score, g.level), self.attr("hud", "panel", True))
        if g.score >= g.high and g.score > 0:
            self.center(y + 7, "NEW HIGH SCORE", self.attr("title3", "panel", True))
        else:
            self.center(y + 7, "HIGH SCORE %06d" % g.high, self.attr("hud_gold", "panel"))
        self.center(y + 8, "%d ghost%s sent back to the cabinets." % (g.banished, "" if g.banished == 1 else "s"),
                    self.attr("ghost", "panel"))
        self.center(y + 10, "N  new shift        Q  quit", self.attr("hud_dim", "panel"))

    def draw_title(self, g):
        self.fill(self.oy, self.ox, VIEW_ROWS, VIEW_COLS, self.attr("hud", "hud_bg"))
        t = g.title_t
        self.big_center(self.oy + 1, "HAUNTED", self.attr("title", "hud_bg", True))
        self.big_center(self.oy + 7, "ARCADE", self.attr("title2", "hud_bg", True))
        self.center(self.oy + 13, "THE ARCADE IS CLOSED. THE MACHINES AREN'T.", self.attr("hud", "hud_bg"))
        self.center(self.oy + 14, "PICK UP THE TRASH. MOP THE SPILLS. MIND THE GHOSTS.", self.attr("hud_dim", "hud_bg"))
        # a row of cabinets along the back wall, one of them acting up
        row = self.oy + 17
        hot = (t // 90) % 8
        for i in range(8):
            x = self.ox + 4 + i * 8
            if i == hot:
                fg = "cab_hot" if (t // 3) % 2 else "cab_hot2"
            else:
                fg = "cab" if math.sin(t / 9.0 + i) > 0.3 else "cab2"
            self.put(row, x, CABINET * 2, self.attr(fg, "hud_bg", i == hot))
        # the floor
        self.put(row + 1, self.ox, "▀" * VIEW_COLS, self.attr("wall", "hud_bg"))
        # the janitor sweeps left to right with the light on; a ghost drifts ahead of him
        jx = self.ox + 2 + (t // 3) % (VIEW_COLS - 6)
        self.put(row + 2, jx, PLAYER, self.attr("player_lit", "hud_bg", True))
        for d in range(1, 5):
            bx = jx + 2 * d
            if bx + 1 < self.ox + VIEW_COLS:
                self.put(row + 2, bx, BEAM, self.attr("beam" if (d + t // 2) % 2 else "beam2", "hud_bg"))
        gx = jx + 11 + int(2 * math.sin(t / 7.0))
        if gx + 1 < self.ox + VIEW_COLS:
            self.put(row + 2, gx, GHOST_FRAMES[(t // 4) % 4], self.attr("scared" if (t // 3) % 2 else "scared2", "hud_bg", True))
        self.center(self.oy + 20, "HIGH SCORE %06d" % g.high, self.attr("hud_gold", "hud_bg", True))
        prompt = "N  CLOCK IN       ?  HOW TO PLAY       Q  QUIT"
        self.center(self.oy + 22, prompt, self.attr("title3" if (t // 15) % 2 else "hud_dim", "hud_bg", (t // 15) % 2 == 1))
