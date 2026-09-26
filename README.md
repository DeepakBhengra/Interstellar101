# Interstellar101

A first-person Panda3D spaceship cockpit that flies through **real astronomical imagery** — NASA / Hubble / Webb galaxies, nebulae, and planetary maps — instead of a fake particle starfield.

You sit behind a windshield. Outside it: a Great Observatories sky, spiral galaxies, colored nebula clouds, textured planets, and an asteroid belt you can actually pass.

## Outside the windshield

- **Sky** — NASA’s 2009 Great Observatories all-sky mosaic wrapped on a sky sphere, so the background is a real star field and galactic structure, not a flat color.
- **Nebulae** — layered, additive clouds you can fly through: Orion (blue), Horsehead, Pillars of Creation (Webb), Helix, Lagoon (red/pink), Carina, and the Veil (purple/red).
- **Galaxies** — Andromeda, the Whirlpool (M51), and the Sombrero hanging in the far distance.
- **Planets** — Venus, Earth + Moon, Mars, Jupiter, Saturn with rings, Neptune, and the Sun, using real surface / atmosphere maps.
- **Asteroids** — a tumbling rock field plus NASA photos of 243 Ida and 433 Eros.

The ship moves through a real 3D volume. Planets stay put, the Moon orbits Earth, and nebulae occupy space you can enter. Hyperdrive widens the FOV and raises the speed cap so the same corridor becomes a fast tour.

## Controls

| Key | Action |
| --- | --- |
| `W` / `S` | Thrust / brake |
| `A` / `D` | Yaw |
| `Q` / `E` | Pitch |
| `Z` / `C` | Roll |
| `Space` | Hyperdrive (hold) |
| `Tab` | Cycle navigation target |
| `F` | Face the current target |
| `R` | Reset to Earth approach |
| `Esc` | Quit |

The HUD on the dashboard shows speed, system / hyperdrive status, the selected nav target and range, and the nearest named object in view.

## Run locally

You need Python 3 and a machine that can open an OpenGL window.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The first launch writes a cockpit overlay and star-glow sprite under `assets/generated/`.

This is a desktop OpenGL app, not a web page.

## Suggested first flight

1. You start on approach to **Earth**, with the Moon nearby and the Orion Nebula off to starboard.
2. Fly past Earth, then through the **asteroid field** (Ida and Eros are marked).
3. Continue toward **Mars**, then the **Pillars of Creation** and **Jupiter**.
4. Hold `Space` to jump the rest of the corridor toward **Saturn**, **Carina**, and **Neptune**.
5. Use `Tab` / `F` if you lose a target.

## Project layout

| Path | Role |
| --- | --- |
| `main.py` | Window, flight, hyperdrive, targeting |
| `world.py` | Sky, planets, nebulae, galaxies, asteroids, stars |
| `cockpit.py` | Windshield frame and HUD |
| `geometry.py` | UV spheres and Saturn’s ring mesh |
| `textures.py` | Texture loading and generated sprites |
| `assets/textures/` | Real NASA / Hubble / Webb / Solar System Scope maps |
| `ATTRIBUTION.md` | Image credits and licenses |

## Stack

- Python 3
- [Panda3D](https://www.panda3d.org/)
- Pillow (cockpit overlay and star glow)

See `ATTRIBUTION.md` for the full image credit list.
