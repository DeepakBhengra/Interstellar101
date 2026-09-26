"""Place real astronomical imagery into the 3D flight volume."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from panda3d.core import (
    AmbientLight,
    CardMaker,
    DirectionalLight,
    PointLight,
    SamplerState,
    TextNode,
    TransparencyAttrib,
    Vec3,
    Vec4,
)

from geometry import make_ring_disc, make_uv_sphere
from textures import (
    load_hud_font,
    load_texture,
    load_texture_path,
    make_cloud_sprite,
    make_cutout_sprite,
    make_ring_texture,
    make_star_glow,
    os_path,
)


@dataclass
class NamedBody:
    name: str
    node: object
    kind: str
    radius: float = 1.0
    label: object = None
    label_range: float = 220.0


@dataclass
class OrbitingMoon:
    node: object
    parent: object
    distance: float
    period: float
    angle: float = 0.0
    incline: float = 12.0


@dataclass
class Spinner:
    node: object
    heading: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0


@dataclass
class SpaceWorld:
    bodies: list = field(default_factory=list)
    moons: list = field(default_factory=list)
    spinners: list = field(default_factory=list)
    sky: object = None
    font: object = None


def _billboard_card(parent, name, width, height):
    cm = CardMaker(name)
    cm.set_frame(-width * 0.5, width * 0.5, -height * 0.5, height * 0.5)
    card = parent.attach_new_node(cm.generate())
    card.set_billboard_point_eye()
    card.set_two_sided(True)
    return card


def _soft_sprite(node, bin_sort=12):
    node.set_light_off()
    node.set_depth_write(False)
    node.set_bin("transparent", bin_sort)
    node.set_transparency(TransparencyAttrib.MAlpha)


def _label(parent, name, z_offset, font):
    text = TextNode(f"label-{name}")
    text.set_text(name)
    text.set_align(TextNode.ACenter)
    text.set_text_color(0.55, 0.95, 1, 0.92)
    if font is not None:
        text.set_font(font)
    node = parent.attach_new_node(text)
    node.set_scale(max(1.4, z_offset * 0.1))
    node.set_z(z_offset)
    node.set_billboard_point_eye()
    node.set_light_off()
    node.set_depth_write(False)
    return node


def build_world(game) -> SpaceWorld:
    world = SpaceWorld()
    rng = random.Random(101)
    world.font = load_hud_font(game.loader)

    _setup_lights(game)
    world.sky = _make_sky(game)
    _make_planets(game, world)
    _make_nebulae(game, world, rng)
    _make_galaxies(game, world)
    _make_asteroids(game, world, rng)
    _make_foreground_stars(game, world, rng)
    return world


def _setup_lights(game):
    ambient = AmbientLight("space-ambient")
    ambient.set_color(Vec4(0.22, 0.24, 0.32, 1))
    game.render.set_light(game.render.attach_new_node(ambient))

    sun = DirectionalLight("sun")
    sun.set_color(Vec4(1.2, 1.08, 0.92, 1))
    sun_np = game.render.attach_new_node(sun)
    sun_np.set_hpr(-55, -18, 0)
    game.render.set_light(sun_np)

    point = PointLight("sun-point")
    point.set_color(Vec4(1.0, 0.85, 0.55, 1))
    point.set_attenuation(Vec3(1, 0.0008, 0.000002))
    point_np = game.render.attach_new_node(point)
    point_np.set_pos(-280, 200, 80)
    game.render.set_light(point_np)


def _make_sky(game):
    sky = make_uv_sphere("sky", radius=9000, rings=24, sectors=48, inside_out=True)
    sky.reparent_to(game.camera)
    sky.set_bin("background", 0)
    sky.set_depth_write(False)
    sky.set_depth_test(False)
    sky.set_light_off()
    sky.set_compass()
    tex = load_texture(game.loader, "sky/great_observatories.jpg", wrap_repeat=True)
    if tex is None:
        tex = load_texture(game.loader, "sky/milky_way.jpg", wrap_repeat=True)
    if tex is not None:
        sky.set_texture(tex, 1)
    sky.set_color(0.95, 0.96, 1.0, 1)
    return sky


def _make_planets(game, world: SpaceWorld):
    catalog = [
        dict(name="Venus", tex="planets/venus.jpg", pos=(-90, 40, 32), radius=9.2, spin=14, atmo=(1.0, 0.82, 0.4, 0.18)),
        dict(name="Earth", tex="planets/earth.jpg", pos=(10, 105, -3), radius=12.0, spin=16, atmo=(0.25, 0.5, 1.0, 0.26)),
        dict(name="Mars", tex="planets/mars.jpg", pos=(-28, 305, 10), radius=8.2, spin=12, atmo=(1.0, 0.45, 0.25, 0.12)),
        dict(name="Jupiter", tex="planets/jupiter.jpg", pos=(62, 530, -12), radius=26.0, spin=22, atmo=(1.0, 0.85, 0.6, 0.1)),
        dict(name="Saturn", tex="planets/saturn.jpg", pos=(-78, 900, 16), radius=20.0, spin=18, atmo=(1.0, 0.9, 0.6, 0.1), rings=True),
        dict(name="Neptune", tex="planets/neptune.jpg", pos=(48, 1220, 42), radius=13.5, spin=10, atmo=(0.3, 0.55, 1.0, 0.2)),
        dict(name="Sun", tex="planets/sun.jpg", pos=(-280, 200, 80), radius=42.0, spin=4, emissive=True),
    ]

    planets = {}
    for spec in catalog:
        body = make_uv_sphere(spec["name"], radius=spec["radius"], rings=28, sectors=48)
        body.reparent_to(game.render)
        body.set_pos(*spec["pos"])
        tex = load_texture(game.loader, spec["tex"], wrap_repeat=True)
        if tex is not None:
            body.set_texture(tex, 1)
        if spec.get("emissive"):
            body.set_light_off()
            body.set_color(1.15, 1.0, 0.75, 1)
            glow = _billboard_card(body, "sun-glow", spec["radius"] * 4.6, spec["radius"] * 4.6)
            try:
                glow_tex = game.loader.load_texture(os_path(make_star_glow(128)))
            except OSError as exc:
                print(f"Could not build sun glow: {exc}")
                glow_tex = None
            if glow_tex is not None:
                glow.set_texture(glow_tex)
            _soft_sprite(glow, 8)
            glow.set_color(1.0, 0.75, 0.25, 0.85)
        if spec.get("atmo") and not spec.get("emissive"):
            shell = make_uv_sphere(f"{spec['name']}-atmo", radius=spec["radius"] * 1.07, rings=16, sectors=24)
            shell.reparent_to(body)
            shell.set_light_off()
            shell.set_transparency(TransparencyAttrib.MAlpha)
            shell.set_bin("transparent", 18)
            r, g, b, a = spec["atmo"]
            shell.set_color(r, g, b, a)
        if spec.get("rings"):
            body.set_p(26)
            rings = make_ring_disc("saturn-rings", spec["radius"] * 1.35, spec["radius"] * 2.45, segments=128)
            rings.reparent_to(body)
            try:
                ring_tex = load_texture_path(game.loader, make_ring_texture(), wrap_repeat=False)
            except OSError as exc:
                print(f"Could not build Saturn rings: {exc}")
                ring_tex = None
            if ring_tex is not None:
                ring_tex.set_wrap_u(SamplerState.WM_repeat)
                ring_tex.set_wrap_v(SamplerState.WM_clamp)
            if ring_tex is not None:
                rings.set_texture(ring_tex, 1)
            rings.set_light_off()
            rings.set_transparency(TransparencyAttrib.MAlpha)
            rings.set_color(1.25, 1.12, 0.88, 1)
            rings.set_two_sided(True)
            rings.set_bin("transparent", 20)
            rings.set_depth_write(False)

        label = _label(body, spec["name"], spec["radius"] + 4.5, world.font)
        world.spinners.append(Spinner(body, heading=spec["spin"]))
        world.bodies.append(
            NamedBody(spec["name"], body, "planet", spec["radius"], label, 320 if spec["name"] != "Sun" else 700)
        )
        planets[spec["name"]] = body

    moon = make_uv_sphere("Moon", radius=3.3, rings=18, sectors=32)
    moon.reparent_to(game.render)
    moon_tex = load_texture(game.loader, "planets/moon.jpg", wrap_repeat=True)
    if moon_tex is not None:
        moon.set_texture(moon_tex, 1)
    label = _label(moon, "Moon", 5.2, world.font)
    world.moons.append(OrbitingMoon(moon, planets["Earth"], distance=28, period=38, angle=40))
    world.spinners.append(Spinner(moon, heading=8))
    world.bodies.append(NamedBody("Moon", moon, "moon", 3.3, label, 160))


def _make_nebulae(game, world: SpaceWorld, rng: random.Random):
    clouds = [
        dict(name="Orion Nebula", tex="nebulae/orion.jpg", pos=(150, 170, 42), size=95, layers=2, reach=170),
        dict(name="Horsehead Nebula", tex="nebulae/horsehead.jpg", pos=(110, 270, -55), size=80, layers=2, reach=160),
        dict(name="Pillars of Creation", tex="nebulae/pillars.jpg", pos=(-170, 360, 55), size=88, layers=2, reach=180),
        dict(name="Helix Nebula", tex="nebulae/helix.jpg", pos=(190, 510, 62), size=75, layers=2, reach=160),
        dict(name="Lagoon Nebula", tex="nebulae/lagoon.jpg", pos=(-140, 610, -48), size=100, layers=2, reach=180),
        dict(name="Carina Nebula", tex="nebulae/carina.jpg", pos=(50, 780, 75), size=130, layers=2, reach=220),
        dict(name="Veil Nebula", tex="nebulae/veil.jpg", pos=(-230, 690, 22), size=110, layers=2, reach=200),
    ]
    for spec in clouds:
        tex = load_texture_path(game.loader, make_cloud_sprite(spec["tex"]))
        root = game.render.attach_new_node(spec["name"])
        root.set_pos(*spec["pos"])
        for i in range(spec["layers"]):
            aspect = 0.64 if "pillars" in spec["tex"] else 1.0
            width = spec["size"] * rng.uniform(0.88, 1.05)
            card = _billboard_card(root, f"{spec['name']}-{i}", width, width * aspect)
            if tex is not None:
                card.set_texture(tex)
            _soft_sprite(card, 14 + i)
            card.set_color(1, 1, 1, 0.92 - i * 0.18)
            card.set_pos(rng.uniform(-8, 8), rng.uniform(-10, 10), rng.uniform(-6, 6))
        label = _label(root, spec["name"], spec["size"] * 0.34, world.font)
        world.bodies.append(NamedBody(spec["name"], root, "nebula", spec["size"] * 0.28, label, spec["reach"]))


def _make_galaxies(game, world: SpaceWorld):
    galaxies = [
        dict(name="Andromeda", tex="galaxies/andromeda.jpg", pos=(-620, 380, 70), size=520, reach=900),
        dict(name="Whirlpool Galaxy", tex="galaxies/whirlpool.jpg", pos=(540, 820, -50), size=260, reach=700),
        dict(name="Sombrero Galaxy", tex="galaxies/sombrero.jpg", pos=(210, 1120, 130), size=220, reach=700),
    ]
    for spec in galaxies:
        tex = load_texture_path(game.loader, make_cloud_sprite(spec["tex"]))
        card = _billboard_card(game.render, spec["name"], spec["size"], spec["size"] * 0.68)
        card.set_pos(*spec["pos"])
        if tex is not None:
            card.set_texture(tex)
        _soft_sprite(card, 10)
        card.set_color(1, 1, 1, 0.95)
        label = _label(card, spec["name"], spec["size"] * 0.26, world.font)
        world.bodies.append(NamedBody(spec["name"], card, "galaxy", spec["size"] * 0.2, label, spec["reach"]))


def _make_asteroids(game, world: SpaceWorld, rng: random.Random):
    moon_tex = load_texture(game.loader, "planets/moon.jpg", wrap_repeat=True)
    heroes = [
        dict(name="243 Ida", tex="asteroids/ida.jpg", pos=(18, 210, -8), size=14),
        dict(name="433 Eros", tex="asteroids/eros.jpg", pos=(-22, 235, 6), size=11),
    ]
    for spec in heroes:
        tex = load_texture_path(game.loader, make_cutout_sprite(spec["tex"]))
        card = _billboard_card(game.render, spec["name"], spec["size"], spec["size"] * 0.72)
        card.set_pos(*spec["pos"])
        if tex is not None:
            card.set_texture(tex)
        _soft_sprite(card, 16)
        label = _label(card, spec["name"], spec["size"] * 0.42, world.font)
        world.bodies.append(NamedBody(spec["name"], card, "asteroid", spec["size"] * 0.4, label, 90))

    field = game.render.attach_new_node("asteroid-field")
    for i in range(55):
        rock = make_uv_sphere(f"rock-{i}", radius=rng.uniform(0.25, 1.1), rings=7, sectors=10)
        rock.reparent_to(field)
        rock.set_pos(
            rng.uniform(-60, 60),
            rng.uniform(175, 285),
            rng.uniform(-22, 22),
        )
        rock.set_scale(rng.uniform(0.7, 1.7), rng.uniform(0.45, 1.15), rng.uniform(0.5, 1.4))
        if moon_tex is not None:
            rock.set_texture(moon_tex, 1)
        rock.set_color(0.42, 0.36, 0.3, 1)
        world.spinners.append(
            Spinner(
                rock,
                heading=rng.uniform(-40, 40),
                pitch=rng.uniform(-25, 25),
                roll=rng.uniform(-30, 30),
            )
        )
    world.bodies.append(NamedBody("Asteroid Field", field, "asteroid", 40, None, 140))


def _make_foreground_stars(game, world: SpaceWorld, rng: random.Random):
    try:
        glow = game.loader.load_texture(os_path(make_star_glow(64)))
    except OSError as exc:
        print(f"Could not build star glow: {exc}")
        glow = None
    colors = [
        (0.75, 0.85, 1.0),
        (1.0, 1.0, 1.0),
        (1.0, 0.92, 0.7),
        (0.65, 0.8, 1.0),
        (1.0, 0.7, 0.55),
    ]
    root = game.render.attach_new_node("near-stars")
    for i in range(220):
        star = _billboard_card(root, f"star-{i}", 1, 1)
        star.set_scale(rng.choice([0.55, 0.75, 1.0, 1.5, 2.2]))
        star.set_pos(
            rng.uniform(-240, 240),
            rng.uniform(-30, 1400),
            rng.uniform(-140, 160),
        )
        if glow is not None:
            star.set_texture(glow)
        _soft_sprite(star, 6)
        color = rng.choice(colors)
        bright = rng.uniform(0.55, 1.15)
        star.set_color(color[0] * bright, color[1] * bright, color[2] * bright, 0.9)


def update_world(world: SpaceWorld, dt: float, camera_pos=None):
    for spinner in world.spinners:
        spinner.node.set_h(spinner.node.get_h() + spinner.heading * dt)
        spinner.node.set_p(spinner.node.get_p() + spinner.pitch * dt)
        spinner.node.set_r(spinner.node.get_r() + spinner.roll * dt)
    for moon in world.moons:
        moon.angle = (moon.angle + 360.0 / moon.period * dt) % 360.0
        rad = math.radians(moon.angle)
        parent = moon.parent.get_pos()
        offset = Vec3(
            math.cos(rad) * moon.distance,
            math.sin(rad) * moon.distance,
            math.sin(rad * 2.0) * math.sin(math.radians(moon.incline)) * 6.0,
        )
        moon.node.set_pos(parent + offset)
    if camera_pos is not None:
        for body in world.bodies:
            if body.label is None:
                continue
            dist = (body.node.get_pos() - camera_pos).length()
            if dist < body.label_range:
                body.label.show()
            else:
                body.label.hide()
