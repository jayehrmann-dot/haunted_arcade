# Haunted Arcade

It's 2 a.m. The arcade is closed, the doors are locked, and you are the janitor.
Pick up the trash, mop the slushie spills, and try not to notice that the
cabinets keep switching themselves on. Atari 2600 looks, single-screen
maze-chase play, running entirely inside your terminal.

```bash
./play.sh
```

or `python3 -m haunted` from this folder. Needs Python 3 (ships with macOS)
and a terminal at least 64 columns by 24 rows. A 256-colour terminal gives the
full palette; 8-colour terminals still work. Hold an arrow key to keep walking;
a fast key-repeat rate in your OS settings makes it smoother.

## The game

The floor is a 32x16 grid of fat pixels. Purple walls, a red front door at the
bottom (that's where you clock in), and twenty-two cyan cabinets along the
walls and in the middle islands, each with its own name on the message line:
Ghoul Gobbler, Space Raiders, Frog Freeway and so on.

- **Trash** (orange) is picked up by walking over it. 10 points.
- **Spills** (blue puddles) have to be mopped: stand on one and press SPACE.
  Three strokes for a slushie, two for ectoplasm. 25 and 40 points.
- **Ghosts** climb out of cabinets. A cabinet flickers red for a second first,
  so you get a warning. They chase you, with a bit of wander. One touch and
  you drop the mop and lose a life. They also leak **ectoplasm** on the carpet
  now and then, which means more mopping.
- **The flashlight** (F) throws a cone six cells long in the direction you are
  facing. A ghost caught in it turns blue and flees. If a fleeing ghost ends
  up next to any cabinet it gets pulled back inside for 50 points. The battery
  lasts about five seconds and recharges while the light is off.
- **The catch:** you cannot pick up trash or mop while the light is on. Light,
  scatter, switch off, clean. Repeat.
- **Levels.** Clear every piece of trash and every spill and the next shift
  starts: more mess, more ghosts, faster ghosts. Bonus 100 x level.
- **Game over** when you run out of lives. An extra life every 5000 points.

The high score is saved to `highscore.json` in this folder.

## Controls

| Key | Action |
| --- | --- |
| Arrows / WASD | Walk. You face the way you last moved |
| Space / M | Mop the spill you are standing on |
| F | Flashlight on / off |
| P | Pause |
| ? | Night shift card (controls and tips) |
| Q / Esc | Quit (asks first) |

## Layout

```
haunted/
  constants.py   layout, tuning, palette, glyphs, block font, cabinet names, janitor lines
  world.py       the floor plan, cabinet parsing, spawn cells
  entities.py    Machine, Ghost, Spill, Janitor
  render.py      curses drawing: block-digit HUD, floor, beam, sprites, overlays
  engine.py      game loop, input, flashlight, ghost AI, levels, scoring
  __main__.py    entry point
highscore.json   created after your first game
```

Difficulty lives in `level_params()` at the top of `constants.py`. The floor
plan is the `MAP` string in `world.py`; any run of `M` on one row becomes a
cabinet, and ghosts come out onto the carpet cells touching it.
