"""Load NASA / Hubble textures and generate the small runtime images."""

from __future__ import annotations

from pathlib import Path

from panda3d.core import Filename, PNMImage, SamplerState, Texture

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


def panda_path(path: Path) -> str:
    """Panda3D wants Unix-style paths even on Windows (/c/Interstellar/...)."""
    filename = Filename.from_os_specific(str(path))
    filename.make_absolute()
    return filename.get_fullpath()


def find_font() -> Path | None:
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def load_hud_font(loader):
    path = find_font()
    if path is None:
        return None
    try:
        return loader.load_font(
            panda_path(path),
            spaceAdvance=1.15,
            lineHeight=1.15,
            pointSize=12,
            pixelsPerUnit=56,
            textureMargin=6,
        )
    except OSError as exc:
        print(f"Could not load HUD font {path}: {exc}")
        return None


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


def _write_pnm(image: PNMImage, path: Path) -> bool:
    return bool(image.write(os_path(path)))


def make_star_glow(size: int = 64) -> Path:
    """Soft white radial sprite for nearby stars."""
    path = ensure_generated_dir() / f"star_glow_{size}.png"
    if path.exists():
        return path
    img = PNMImage(size, size, 4)
    img.fill(0, 0, 0)
    img.alpha_fill(0)
    cx = cy = (size - 1) / 2.0
    radius = size / 2.0
    for y in range(size):
        for x in range(size):
            dx = (x - cx) / radius
            dy = (y - cy) / radius
            dist = (dx * dx + dy * dy) ** 0.5
            core = max(0.0, 1.0 - dist)
            alpha = core**2.6
            shade = min(1.0, core * 1.15)
            img.set_xel(x, y, shade, 0.96 * shade + 0.04, shade)
            img.set_alpha(x, y, alpha)
    if not _write_pnm(img, path):
        raise OSError(f"Could not write star glow: {path}")
    return path


def make_cloud_sprite(relative: str) -> Path:
    """Cut a nebula/galaxy photo into a soft-edged sprite. Falls back to the original."""
    source = TEXTURE_ROOT / relative
    dest = ensure_generated_dir() / f"{Path(relative).stem}_cloud.png"
    if _fresh(dest, source):
        return dest
    src = PNMImage()
    if not source.exists() or not src.read(os_path(source)):
        return source
    if not src.has_alpha():
        src.add_alpha()
    width, height = src.get_x_size(), src.get_y_size()
    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
    radius = min(cx, cy) * 0.92
    for y in range(height):
        for x in range(width):
            red = src.get_red(x, y)
            green = src.get_green(x, y)
            blue = src.get_blue(x, y)
            luma = 0.3 * red + 0.59 * green + 0.11 * blue
            alpha = max(0.0, min(1.0, (luma - 0.04) / 0.7))
            dx, dy = (x - cx) / radius, (y - cy) / radius
            vig = max(0.0, 1.0 - (dx * dx + dy * dy) ** 1.1)
            src.set_alpha(x, y, alpha * vig)
    if not _write_pnm(src, dest):
        return source
    return dest


def make_cutout_sprite(relative: str) -> Path:
    """Keep a photographed asteroid and drop the black space around it."""
    source = TEXTURE_ROOT / relative
    dest = ensure_generated_dir() / f"{Path(relative).stem}_cutout.png"
    if _fresh(dest, source):
        return dest
    src = PNMImage()
    if not source.exists() or not src.read(os_path(source)):
        return source
    if not src.has_alpha():
        src.add_alpha()
    for y in range(src.get_y_size()):
        for x in range(src.get_x_size()):
            luma = (
                0.3 * src.get_red(x, y)
                + 0.59 * src.get_green(x, y)
                + 0.11 * src.get_blue(x, y)
            )
            if luma < 0.03:
                alpha = 0.0
            elif luma > 0.09:
                alpha = 1.0
            else:
                alpha = (luma - 0.03) / 0.06
            src.set_alpha(x, y, alpha)
    if not _write_pnm(src, dest):
        return source
    return dest


def make_ring_texture() -> Path:
    """Build a radial Saturn-ring profile (U wraps around, V is radius)."""
    dest = ensure_generated_dir() / "saturn_rings.png"
    if dest.exists():
        return dest

    width, height = 8, 256
    img = PNMImage(width, height, 4)
    img.fill(0, 0, 0)
    img.alpha_fill(0)
    for y in range(height):
        t = y / (height - 1)
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
        red = min(1.0, 0.90 * bands + 0.08)
        green = min(1.0, 0.80 * bands + 0.05)
        blue = 0.59 * bands
        for x in range(width):
            img.set_xel(x, y, red, green, blue)
            img.set_alpha(x, y, bands)
    if not _write_pnm(img, dest):
        raise OSError(f"Could not write Saturn rings: {dest}")
    return dest


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def apply_texture(node, tex: Texture | None, color=None) -> None:
    if tex is not None:
        node.set_texture(tex, 1)
    if color is not None:
        node.set_color(*color)
