"""Layout, tuning, palette, glyphs, block font and flavour text for Haunted Arcade."""

FPS = 30
TICK = 1.0 / FPS

# ---------------------------------------------------------------- screen layout
# Everything is drawn inside a 64x24 window centred in the terminal.
VIEW_COLS = 64
HUD_ROWS = 5                 # the big block-digit score lives here
GAP_ROWS = 1
FIELD_ROWS = 16
MSG_ROWS = 2
VIEW_ROWS = HUD_ROWS + GAP_ROWS + FIELD_ROWS + MSG_ROWS      # 24 terminal rows
FIELD_TOP = HUD_ROWS + GAP_ROWS                              # first field row (6)
MSG_TOP = FIELD_TOP + FIELD_ROWS                             # first message row (22)

# ---------------------------------------------------------------- playfield
# The arcade floor is a grid of fat Atari pixels: each cell is CELL_W columns
# wide and one row tall, so a 32x16 grid fills the 64-column view.
FIELD_W = 32
FIELD_H = 16
CELL_W = 2

# ---------------------------------------------------------------- tuning
START_LIVES = 3
EXTRA_LIFE_EVERY = 5000
MOVE_COOLDOWN = 3            # ticks between janitor steps (10 cells per second)
SCRUB_COOLDOWN = 5           # ticks between mop strokes
SCRUBS_PER_SPILL = 3
SCRUBS_PER_ECTO = 2
BEAM_LENGTH = 6              # cells the flashlight reaches
BATTERY_MAX = 100.0
BATTERY_DRAIN = 0.6          # per tick with the light on (about 5.5 s of light)
BATTERY_CHARGE = 0.35        # per tick with the light off
BATTERY_MIN_ON = 20.0        # it won't switch on below this
SCARE_TICKS = 45             # how long a ghost keeps fleeing after the beam leaves it
CHARGE_TICKS = 30            # a cabinet flickers this long before a ghost climbs out
DEATH_TICKS = 45
INVULN_TICKS = 60
BANNER_TICKS = 75
ECTO_CHANCE = 0.004          # per ghost per tick: chance it leaves ectoplasm behind
ECTO_EXTRA_CAP = 3           # ghosts can add at most this many spills beyond the level's own

SCORE = {"trash": 10, "spill": 25, "ecto": 40, "banish": 50, "level": 100}


def level_params(n):
    """How much mess, how many ghosts and how fast they are on level n."""
    return {
        "trash": min(8 + 2 * (n - 1), 20),
        "spills": min(3 + (n - 1), 8),
        "max_ghosts": min(2 + (n - 1), 7),
        "spawn_ticks": max(60, 180 - 20 * (n - 1)),
        "period": max(4, 9 - (n - 1)),          # ticks per ghost step
    }


# ---------------------------------------------------------------- palette
# name -> (256-colour index, basic 8-colour index)
# basic: 0 black 1 red 2 green 3 yellow 4 blue 5 magenta 6 cyan 7 white
PALETTE = {
    "floor":      (233, 0),
    "floor2":     (234, 0),
    "wall":       (93, 5),
    "door":       (160, 1),
    "door2":      (214, 3),

    "cab":        (31, 6),
    "cab2":       (37, 6),
    "cab_hot":    (196, 1),
    "cab_hot2":   (231, 7),

    "player":     (220, 3),
    "player_lit": (231, 7),
    "ghost":      (255, 7),
    "ghost_dim":  (250, 7),
    "scared":     (27, 4),
    "scared2":    (75, 6),

    "trash":      (172, 2),
    "trash2":     (214, 2),
    "spill":      (33, 4),
    "spill2":     (39, 4),
    "spill3":     (45, 6),
    "ecto":       (46, 2),
    "ecto2":      (82, 2),
    "beam":       (178, 3),
    "beam2":      (226, 3),

    "hud_bg":     (16, 0),
    "hud":        (231, 7),
    "hud_dim":    (245, 7),
    "hud_gold":   (220, 3),
    "hud_red":    (196, 1),
    "msg":        (159, 6),
    "msg_alert":  (203, 1),
    "msg_good":   (120, 2),
    "panel":      (16, 0),
    "panel_fg":   (231, 7),
    "title":      (201, 5),
    "title2":     (51, 6),
    "title3":     (220, 3),
}

# ---------------------------------------------------------------- glyphs
# Every sprite is one cell: two terminal characters.
PLAYER = "▐▌"
GHOST_FRAMES = ("▟▙", "▟▙", "▟▙", "▚▞")      # the odd frame is a shimmer
CABINET = "▛▜"
WALL = "██"
TRASH = "▚▞"
SPILL = ("··", "░░", "▒▒")                   # indexed by remaining scrubs - 1
ECTO = ("~~", "≈≈")
BEAM = "░░"
LIFE_ICON = "▐▌"

# ---------------------------------------------------------------- 3x5 block font
FONT = {
    "A": (" █ ", "█ █", "███", "█ █", "█ █"),
    "B": ("██ ", "█ █", "██ ", "█ █", "██ "),
    "C": (" ██", "█  ", "█  ", "█  ", " ██"),
    "D": ("██ ", "█ █", "█ █", "█ █", "██ "),
    "E": ("███", "█  ", "██ ", "█  ", "███"),
    "F": ("███", "█  ", "██ ", "█  ", "█  "),
    "G": (" ██", "█  ", "█ █", "█ █", " ██"),
    "H": ("█ █", "█ █", "███", "█ █", "█ █"),
    "I": ("███", " █ ", " █ ", " █ ", "███"),
    "J": ("  █", "  █", "  █", "█ █", " █ "),
    "K": ("█ █", "█ █", "██ ", "█ █", "█ █"),
    "L": ("█  ", "█  ", "█  ", "█  ", "███"),
    "M": ("█ █", "███", "███", "█ █", "█ █"),
    "N": ("██ ", "█ █", "█ █", "█ █", "█ █"),
    "O": ("███", "█ █", "█ █", "█ █", "███"),
    "P": ("██ ", "█ █", "██ ", "█  ", "█  "),
    "Q": ("███", "█ █", "█ █", "███", "  █"),
    "R": ("██ ", "█ █", "██ ", "█ █", "█ █"),
    "S": (" ██", "█  ", " █ ", "  █", "██ "),
    "T": ("███", " █ ", " █ ", " █ ", " █ "),
    "U": ("█ █", "█ █", "█ █", "█ █", "███"),
    "V": ("█ █", "█ █", "█ █", "█ █", " █ "),
    "W": ("█ █", "█ █", "███", "███", "█ █"),
    "X": ("█ █", "█ █", " █ ", "█ █", "█ █"),
    "Y": ("█ █", "█ █", " █ ", " █ ", " █ "),
    "Z": ("███", "  █", " █ ", "█  ", "███"),
    "0": ("███", "█ █", "█ █", "█ █", "███"),
    "1": (" █ ", "██ ", " █ ", " █ ", "███"),
    "2": ("███", "  █", "███", "█  ", "███"),
    "3": ("███", "  █", "███", "  █", "███"),
    "4": ("█ █", "█ █", "███", "  █", "  █"),
    "5": ("███", "█  ", "███", "  █", "███"),
    "6": ("█  ", "█  ", "███", "█ █", "███"),
    "7": ("███", "  █", "  █", "  █", "  █"),
    "8": ("███", "█ █", "███", "█ █", "███"),
    "9": ("███", "█ █", "███", "  █", "███"),
    "!": (" █ ", " █ ", " █ ", "   ", " █ "),
    "-": ("   ", "   ", "███", "   ", "   "),
    " ": ("   ", "   ", "   ", "   ", "   "),
}

# ---------------------------------------------------------------- the cabinets
# Fake 1982 arcade games, one name per cabinet, assigned in map order.
MACHINE_NAMES = [
    "GHOUL GOBBLER", "SPACE RAIDERS", "MOAT CROSSER", "PIXEL PANIC",
    "COSMIC CRYPT", "TOMB TUMBLER", "LASER LARRY", "DUNGEON DASH",
    "ASTRO BLASTER", "FROG FREEWAY", "MISSILE MAYHEM", "BAT ATTACK",
    "GRAVE DIGGER", "NEON NINJA", "ROBOT RUMBLE", "SKULL SKIPPER",
    "WARP WARRIOR", "CENTIPEDE CAVE", "HAUNTED HOOPS", "PAC-RAT",
    "DIG DIG DIG", "ZOMBIE ZAPPER",
]

# ---------------------------------------------------------------- janitor's log
LINES_START = [
    "Doors locked. Lights off. Mop ready. Let's get this over with.",
    "Night shift. Just me, the mop, and twenty-two humming cabinets.",
]
LINES_LEVEL = [
    "All clean. For now. More of them clocked in.",
    "Floor's spotless. The cabinets disagree.",
    "Next room. Same mop. More ghosts.",
]
LINES_STIR = [
    "Something's stirring in {name}.",
    "{name} just switched itself on.",
    "The screen on {name} is glowing. Nobody's playing it.",
    "{name} is making that noise again.",
]
LINES_BANISH = [
    "Back in the cabinet, pal.",
    "Lights out for you.",
    "{name} swallowed it whole.",
    "Not in my arcade.",
    "Go haunt a high score.",
]
LINES_SPILL = [
    "Spill mopped. Who spills a slushie after closing?",
    "Clean. Finally.",
    "One less puddle.",
]
LINES_ECTO = [
    "Ectoplasm mopped. That's going on the report.",
    "Ecto's gone. The mop will never be the same.",
]
LINES_ECTO_DROP = [
    "Great. That one's leaking ectoplasm.",
    "Something slimy just hit the floor.",
]
LINES_BUSY = [
    "Can't clean with the flashlight on!",
    "Mop OR flashlight. I only have two hands.",
]
LINES_DEAD_BATTERY = [
    "Flashlight's dead. Give it a second.",
    "Click. Click. Nothing. Come on, batteries.",
]
LINES_HIT = [
    "Boo. Dropped the mop.",
    "Cold hands. Cold, see-through hands.",
    "It went right through me. I felt that in my fillings.",
    "Okay. OKAY. Nobody saw that.",
]
LINES_IDLE = [
    "The jukebox is playing by itself again.",
    "Tip: ghosts hate the flashlight. So does the mop.",
    "The high score on {name} just changed. Nobody's here.",
    "Is it midnight yet? It feels like it's been midnight for hours.",
    "Somebody left a quarter in {name}. It keeps spending itself.",
    "Tip: a scared ghost near a cabinet gets pulled back inside.",
    "Tip: stand on a puddle and press SPACE to mop. Three strokes.",
    "The change machine just gave me a token I didn't ask for.",
    "Every screen in here says GAME OVER. I didn't do that.",
]
LINES_EXTRA = [
    "Found a spare set of coveralls in the back. Extra life!",
]
