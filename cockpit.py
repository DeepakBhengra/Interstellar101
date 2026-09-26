"""Cockpit windshield overlay and HUD chrome."""

from __future__ import annotations

from pathlib import Path

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import CardMaker, PNMImage, SamplerState, TextNode, TransparencyAttrib

from textures import ensure_generated_dir, load_hud_font, os_path


def _in_polygon(x: float, y: float, pts: list[tuple[float, float]]) -> bool:
    inside = False
    last_x, last_y = pts[-1]
    for px, py in pts:
        if (py > y) != (last_y > y):
            cross = (last_x - px) * (y - py) / ((last_y - py) or 1e-6) + px
            if x < cross:
                inside = not inside
        last_x, last_y = px, py
    return inside


def _fill_rect(img: PNMImage, x0, y0, x1, y1, color, alpha):
    width, height = img.get_x_size(), img.get_y_size()
    x0, x1 = max(0, int(x0)), min(width, int(x1))
    y0, y1 = max(0, int(y0)), min(height, int(y1))
    red, green, blue = color
    for y in range(y0, y1):
        for x in range(x0, x1):
            img.set_xel(x, y, red, green, blue)
            img.set_alpha(x, y, alpha)


def make_cockpit_overlay(size=(1280, 720)) -> Path:
    """Dark metal canopy with a hexagonal windshield cutout."""
    path = ensure_generated_dir() / "cockpit.png"
    if path.exists():
        return path

    width, height = size
    img = PNMImage(width, height, 4)
    img.fill(0.03, 0.04, 0.06)
    img.alpha_fill(0.92)

    inset_x, inset_top, inset_bot = 140, 52, 168
    hex_pts = [
        (inset_x + 60, inset_top),
        (width - inset_x - 60, inset_top),
        (width - inset_x + 12, height * 0.42),
        (width - inset_x - 28, height - inset_bot),
        (inset_x + 28, height - inset_bot),
        (inset_x - 12, height * 0.42),
    ]

    for y in range(inset_top, height - inset_bot + 8):
        for x in range(inset_x - 20, width - inset_x + 20):
            if not _in_polygon(x, y, hex_pts):
                continue
            edge = (
                not _in_polygon(x - 5, y, hex_pts)
                or not _in_polygon(x + 5, y, hex_pts)
                or not _in_polygon(x, y - 5, hex_pts)
                or not _in_polygon(x, y + 5, hex_pts)
            )
            if edge:
                img.set_xel(x, y, 0.20, 0.82, 0.92)
                img.set_alpha(x, y, 0.85)
            else:
                img.set_xel(x, y, 0.015, 0.07, 0.12)
                img.set_alpha(x, y, 0.06)

    _fill_rect(img, 0, 0, width, 44, (0.025, 0.035, 0.055), 0.96)
    _fill_rect(img, 0, 42, width, 46, (0.16, 0.75, 0.86), 0.75)
    _fill_rect(img, 0, height - 150, width, height, (0.027, 0.039, 0.059), 0.97)
    _fill_rect(img, 120, height - 168, width - 120, height - 148, (0.027, 0.039, 0.059), 0.97)
    _fill_rect(img, 120, height - 168, width - 120, height - 165, (0.20, 0.82, 0.90), 0.8)
    _fill_rect(img, 32, height - 136, 280, height - 24, (0.045, 0.07, 0.09), 0.88)
    _fill_rect(img, width - 280, height - 136, width - 32, height - 24, (0.045, 0.07, 0.09), 0.88)
    _fill_rect(img, width * 0.5 - 150, height - 128, width * 0.5 + 150, height - 30, (0.045, 0.07, 0.09), 0.82)

    if not img.write(os_path(path)):
        raise OSError(f"Could not write cockpit overlay: {path}")
    return path


class CockpitHUD:
    def __init__(self, base):
        self.overlay = None
        try:
            overlay_path = make_cockpit_overlay()
            tex = base.loader.load_texture(os_path(overlay_path))
            if tex is not None:
                tex.set_minfilter(SamplerState.FT_linear)
                tex.set_magfilter(SamplerState.FT_linear)
                cm = CardMaker("cockpit-overlay")
                cm.set_frame(-1, 1, -1, 1)
                self.overlay = base.render2d.attach_new_node(cm.generate())
                self.overlay.set_texture(tex)
                self.overlay.set_transparency(TransparencyAttrib.MAlpha)
                self.overlay.set_bin("fixed", 50)
                self.overlay.set_depth_test(False)
                self.overlay.set_depth_write(False)
        except OSError as exc:
            print(f"Could not build cockpit overlay: {exc}")

        cyan = (0.25, 0.95, 1, 1)
        dim = (0.55, 0.75, 0.85, 1)
        warn = (1.0, 0.55, 0.18, 1)
        font = load_hud_font(base.loader)

        def label(text, pos, scale, fg, align):
            return OnscreenText(
                text=text,
                pos=pos,
                scale=scale,
                fg=fg,
                align=align,
                font=font,
                mayChange=True,
            )

        self.title = label("INTERSTELLAR", (0, 0.93), 0.046, cyan, TextNode.ACenter)
        self.status = label("SYSTEM / ONLINE", (-1.28, 0.93), 0.03, (0.35, 1.0, 0.7, 1), TextNode.ALeft)
        self.speed = label("SPD / 000", (1.28, 0.93), 0.036, cyan, TextNode.ARight)
        self.destination = label("NAV / EARTH", (-1.05, -0.78), 0.036, cyan, TextNode.ALeft)
        self.distance = label("RANGE / ---", (-1.05, -0.86), 0.03, dim, TextNode.ALeft)
        self.nearest = label("VISUAL / ---", (1.05, -0.78), 0.032, cyan, TextNode.ARight)
        self.hint = label(
            "WS thrust | AD yaw | QE pitch | ZC roll | TAB target | F face | SPACE hyperdrive",
            (0, -0.95),
            0.028,
            (0.55, 0.7, 0.8, 1),
            TextNode.ACenter,
        )
        self.warn_color = warn
        self.cyan = cyan

    def update(self, speed: float, hyperdrive: bool, dest_name: str, dest_range: float, visual: str):
        self.speed.setText(f"SPD / {int(speed):03d}")
        self.destination.setText(f"NAV / {dest_name.upper()}")
        self.distance.setText(f"RANGE / {dest_range:,.0f}")
        self.nearest.setText(f"VISUAL / {visual.upper()}")
        if hyperdrive:
            self.status.setText("HYPERDRIVE / ENGAGED")
            self.status.setFg(self.warn_color)
            self.title.setFg(self.warn_color)
        else:
            self.status.setText("SYSTEM / ONLINE")
            self.status.setFg((0.35, 1.0, 0.7, 1))
            self.title.setFg(self.cyan)
