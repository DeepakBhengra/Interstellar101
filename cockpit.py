"""Cockpit windshield overlay and HUD chrome."""

from __future__ import annotations

from pathlib import Path

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import CardMaker, SamplerState, TextNode, TransparencyAttrib

from textures import ensure_generated_dir, load_hud_font, os_path


def make_cockpit_overlay(size=(1920, 1080)) -> Path:
    """Dark metal canopy with a hexagonal windshield cutout."""
    from PIL import Image, ImageDraw, ImageFilter

    path = ensure_generated_dir() / "cockpit.png"
    if path.exists():
        return path

    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Hexagonal windshield opening (transparent glass)
    inset_x, inset_top, inset_bot = 210, 78, 250
    hex_pts = [
        (inset_x + 90, inset_top),
        (w - inset_x - 90, inset_top),
        (w - inset_x + 20, h * 0.42),
        (w - inset_x - 40, h - inset_bot),
        (inset_x + 40, h - inset_bot),
        (inset_x - 20, h * 0.42),
    ]

    # Opaque hull everywhere except the glass
    hull = Image.new("RGBA", (w, h), (8, 11, 16, 235))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(hex_pts, fill=255)
    hull.putalpha(235)
    clear = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hull = Image.composite(clear, hull, mask)
    img.alpha_composite(hull)

    # Inner cyan rim around the glass
    rim = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rim_draw = ImageDraw.Draw(rim)
    rim_draw.polygon(hex_pts, outline=(90, 230, 255, 210), width=6)
    rim_draw.polygon(hex_pts, outline=(20, 80, 110, 160), width=14)
    img.alpha_composite(rim.filter(ImageFilter.GaussianBlur(1.2)))

    # Canopy struts
    draw = ImageDraw.Draw(img)
    strut_color = (18, 24, 32, 230)
    draw.line((w * 0.5, inset_top, w * 0.5, inset_top + 36), fill=strut_color, width=10)
    draw.line((inset_x + 40, h - inset_bot, w * 0.5, h * 0.62), fill=(16, 22, 30, 120), width=3)
    draw.line((w - inset_x - 40, h - inset_bot, w * 0.5, h * 0.62), fill=(16, 22, 30, 120), width=3)

    # Top status rail
    draw.rectangle((0, 0, w, 64), fill=(6, 9, 14, 245))
    draw.rectangle((0, 62, w, 66), fill=(40, 190, 220, 180))

    # Bottom instrument shelf
    draw.polygon(
        [
            (0, h),
            (0, h - 210),
            (180, h - 250),
            (w - 180, h - 250),
            (w, h - 210),
            (w, h),
        ],
        fill=(7, 10, 15, 250),
    )
    draw.line((180, h - 250, w - 180, h - 250), fill=(50, 210, 230, 200), width=3)

    # Corner brackets
    bracket = (70, 220, 240, 200)
    for x0, x1 in ((36, 150), (w - 150, w - 36)):
        draw.rectangle((x0, 80, x1, 84), fill=bracket)
        draw.rectangle((x0 if x0 < w / 2 else x1 - 4, 80, x0 + 4 if x0 < w / 2 else x1, 150), fill=bracket)

    # Glass vignette so the hull reads as a windshield, not a UI box
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    vdraw.polygon(hex_pts, fill=(4, 18, 32, 38))
    img.alpha_composite(vignette)

    # Soft dirt / reflection streaks on the glass
    streaks = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(streaks)
    sdraw.line((w * 0.22, h * 0.18, w * 0.38, h * 0.55), fill=(180, 220, 255, 18), width=2)
    sdraw.line((w * 0.70, h * 0.16, w * 0.78, h * 0.42), fill=(180, 220, 255, 14), width=2)
    img.alpha_composite(streaks)

    # Instrument wells on the dashboard
    well = (12, 18, 24, 220)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((48, h - 200, 420, h - 36), radius=12, fill=well, outline=(40, 160, 180, 160), width=2)
    draw.rounded_rectangle((w - 420, h - 200, w - 48, h - 36), radius=12, fill=well, outline=(40, 160, 180, 160), width=2)
    draw.rounded_rectangle((w * 0.5 - 220, h - 190, w * 0.5 + 220, h - 44), radius=10, fill=well, outline=(40, 160, 180, 120), width=1)

    img.save(path)
    return path


class CockpitHUD:
    def __init__(self, base):
        overlay_path = make_cockpit_overlay()
        tex = base.loader.load_texture(os_path(overlay_path))
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
