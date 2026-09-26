"""Load NASA / Hubble textures and generate the small runtime images."""

from __future__ import annotations

from pathlib import Path

from panda3d.core import Filename, SamplerState, Texture

ROOT = Path(__file__).resolve().parent
TEXTURE_ROOT = ROOT / "assets" / "textures"
GENERATED = ROOT / "assets" / "generated"
FONT_CANDIDATES = [
    ROOT / "assets" / "fonts" / "DejaVuSans.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
]


def os_path(path: Path) -> Filename:
    return Filename.from_os_specific(str(path))


def find_font() -> Path | None:
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def load_hud_font(loader):
    path = find_font()
    if path is None:
        return None
    return loader.load_font(
        str(path),
        spaceAdvance=1.15,
        lineHeight=1.15,
        pointSize=12,
        pixelsPerUnit=56,
        textureMargin=6,
    )


def load_texture(loader, relative: str, wrap_repeat: bool = False) -> Texture | None:
    path = TEXTURE_ROOT / relative
    if not path.exists():
        print(f"Missing texture: {path}")
        return None
    return load_texture_path(loader, path, wrap_repeat)


def load_texture_path(loader, path: Path, wrap_repeat: bool = False) -> Texture | None:
    if not path.exists():
        print(f"Missing texture: {path}")
        return None
    tex = loader.load_texture(os_path(path))
    if tex is None:
        print(f"Failed to load texture: {path}")
        return None
    tex.set_minfilter(SamplerState.FT_linear_mipmap_linear)
    tex.set_magfilter(SamplerState.FT_linear)
    wrap = SamplerState.WM_repeat if wrap_repeat else SamplerState.WM_clamp
    tex.set_wrap_u(wrap)
    tex.set_wrap_v(SamplerState.WM_clamp if not wrap_repeat else wrap)
    return tex


def ensure_generated_dir() -> Path:
    GENERATED.mkdir(parents=True, exist_ok=True)
    return GENERATED


def _fresh(dest: Path, source: Path) -> bool:
    return dest.exists() and dest.stat().st_mtime >= source.stat().st_mtime


def make_star_glow(size: int = 64) -> Path:
    """Soft white radial sprite for nearby stars."""
    from PIL import Image

    path = ensure_generated_dir() / f"star_glow_{size}.png"
    if path.exists():
        return path
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx = cy = (size - 1) / 2.0
    radius = size / 2.0
    pixels = img.load()
    for y in range(size):
        for x in range(size):
            dx = (x - cx) / radius
            dy = (y - cy) / radius
            d = (dx * dx + dy * dy) ** 0.5
            core = max(0.0, 1.0 - d)
            alpha = core**2.6
            shade = min(1.0, core * 1.15)
            pixels[x, y] = (
                int(255 * shade),
                int(245 * shade + 10),
                int(255 * shade),
                int(255 * alpha),
            )
    img.save(path)
    return path


def _radial_mask(size: tuple[int, int], power: float = 2.2):
    from PIL import Image

    small = Image.new("L", (256, 256))
    pixels = small.load()
    center = 127.5
    for y in range(256):
        for x in range(256):
            dist = ((x - center) ** 2 + (y - center) ** 2) ** 0.5 / center
            pixels[x, y] = int(255 * max(0.0, 1.0 - dist**power))
    return small.resize(size, Image.Resampling.BICUBIC)


def make_cloud_sprite(relative: str) -> Path:
    """Cut a nebula/galaxy photo into a soft-edged glowing sprite."""
    from PIL import Image, ImageChops, ImageFilter

    source = TEXTURE_ROOT / relative
    dest = ensure_generated_dir() / f"{Path(relative).stem}_cloud.png"
    if _fresh(dest, source):
        return dest

    rgb = Image.open(source).convert("RGB")
    rgb.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
    luma = rgb.convert("L").point(lambda p: 0 if p < 10 else min(255, int((p - 8) * 1.2)))
    luma = luma.filter(ImageFilter.GaussianBlur(1.2))
    alpha = ImageChops.multiply(luma, _radial_mask(rgb.size))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    out.save(dest)
    return dest


def make_cutout_sprite(relative: str) -> Path:
    """Keep a photographed asteroid and drop the black space around it."""
    from PIL import Image, ImageFilter

    source = TEXTURE_ROOT / relative
    dest = ensure_generated_dir() / f"{Path(relative).stem}_cutout.png"
    if _fresh(dest, source):
        return dest

    rgb = Image.open(source).convert("RGB")
    rgb.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
    luma = rgb.convert("L")
    alpha = luma.point(lambda p: 0 if p < 8 else 255 if p > 22 else int((p - 8) * 18))
    alpha = alpha.filter(ImageFilter.GaussianBlur(1.0))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    out.save(dest)
    return dest


def make_ring_texture() -> Path:
    """Build a radial Saturn-ring profile (U wraps around, V is radius)."""
    from PIL import Image

    dest = ensure_generated_dir() / "saturn_rings.png"
    if dest.exists():
        return dest

    width, height = 8, 256
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = img.load()
    for y in range(height):
        t = y / (height - 1)
        # Cassini-like gaps so the rings read as rings, not a disc
        bands = (
            0.08
            + 0.75 * _smoothstep(0.04, 0.16, t)
            - 0.62 * _smoothstep(0.28, 0.33, t)
            + 0.55 * _smoothstep(0.36, 0.48, t)
            - 0.45 * _smoothstep(0.58, 0.63, t)
            + 0.38 * _smoothstep(0.66, 0.82, t)
            - 0.35 * _smoothstep(0.90, 0.99, t)
        )
        bands = max(0.0, min(1.0, bands))
        color = (
            int(230 * bands + 20),
            int(205 * bands + 12),
            int(150 * bands),
            int(255 * bands),
        )
        for x in range(width):
            pixels[x, y] = color
    img.save(dest)
    return dest


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def apply_texture(node, tex: Texture | None, color=None) -> None:
    if tex is not None:
        node.set_texture(tex, 1)
    if color is not None:
        node.set_color(*color)
