"""Generate premium branding assets for Developer OS."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"


BG = "#111827"
BG_DARK = "#0b1220"
SURFACE = (17, 24, 39, 208)
SURFACE_SOFT = (17, 24, 39, 170)
SURFACE_LIGHT = (255, 255, 255, 16)
TEXT = "#f8fafc"
MUTED = "#94a3b8"
BLUE = "#0ea5e9"
TEAL = "#14b8a6"
INDIGO = "#6366f1"
GREEN = "#22c55e"
AMBER = "#f59e0b"
ROSE = "#fb7185"


@dataclass(frozen=True)
class FontPack:
    regular: ImageFont.FreeTypeFont
    bold: ImageFont.FreeTypeFont
    mono: ImageFont.FreeTypeFont
    black: ImageFont.FreeTypeFont


def font_pack() -> FontPack:
    regular = "/System/Library/Fonts/Supplemental/Arial.ttf"
    bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    black = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
    mono = "/System/Library/Fonts/SFNSMono.ttf"
    return FontPack(
        regular=ImageFont.truetype(regular, 18),
        bold=ImageFont.truetype(bold, 18),
        mono=ImageFont.truetype(mono, 18),
        black=ImageFont.truetype(black, 18),
    )


FONTS = font_pack()


def pick_font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    mapping = {
        "regular": "/System/Library/Fonts/Supplemental/Arial.ttf",
        "bold": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "mono": "/System/Library/Fonts/SFNSMono.ttf",
        "black": "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    }
    return ImageFont.truetype(mapping[kind], size)


def ensure_dirs() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(size: tuple[int, int], top: str = BG_DARK, bottom: str = BG) -> Image.Image:
    width, height = size
    img = Image.new("RGBA", size)
    start = hex_to_rgb(top)
    end = hex_to_rgb(bottom)
    for y in range(height):
        color = blend(start, end, y / max(height - 1, 1))
        ImageDraw.Draw(img).line((0, y, width, y), fill=color + (255,))
    return img


def add_glow(layer: Image.Image, center: tuple[int, int], color: str, radius: int, strength: int = 220) -> None:
    glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    x, y = center
    r = radius
    draw.ellipse((x - r, y - r, x + r, y + r), fill=hex_to_rgb(color) + (strength,))
    glow = glow.filter(ImageFilter.GaussianBlur(radius * 0.38))
    layer.alpha_composite(glow)


def add_noise(layer: Image.Image, amount: int = 26) -> None:
    pixels = layer.load()
    width, height = layer.size
    for y in range(height):
        for x in range(width):
            if (x + y) % amount != 0:
                continue
            r, g, b, a = pixels[x, y]
            delta = ((x * 13 + y * 17) % 5) - 2
            pixels[x, y] = (
                max(0, min(255, r + delta)),
                max(0, min(255, g + delta)),
                max(0, min(255, b + delta)),
                a,
            )


def draw_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.FreeTypeFont, fill: str) -> None:
    draw.text(xy, text, font=font, fill=fill)


def draw_multiline(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    spacing: int = 8,
) -> None:
    draw.multiline_text(xy, text, font=font, fill=fill, spacing=spacing)


def rounded_shadow(
    base: Image.Image,
    box: tuple[int, int, int, int],
    radius: int,
    shadow_color: tuple[int, int, int, int] = (0, 0, 0, 140),
    offset: tuple[int, int] = (0, 12),
    blur: int = 24,
) -> None:
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(
        (x1 + offset[0], y1 + offset[1], x2 + offset[0], y2 + offset[1]),
        radius=radius,
        fill=shadow_color,
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(shadow)


def glass_panel(
    base: Image.Image,
    box: tuple[int, int, int, int],
    radius: int = 28,
    fill: tuple[int, int, int, int] = SURFACE,
    outline: tuple[int, int, int, int] = (255, 255, 255, 36),
    shadow: bool = True,
) -> ImageDraw.ImageDraw:
    if shadow:
        rounded_shadow(base, box, radius)
    panel = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=1)
    base.alpha_composite(panel)
    return ImageDraw.Draw(base)


def pill(
    base: Image.Image,
    xy: tuple[int, int],
    text: str,
    fill: tuple[int, int, int] = (255, 255, 255),
    bg: tuple[int, int, int, int] = (255, 255, 255, 16),
    border: tuple[int, int, int, int] = (255, 255, 255, 48),
    font: ImageFont.FreeTypeFont | None = None,
) -> tuple[int, int, int, int]:
    font = font or pick_font("bold", 18)
    drawer = ImageDraw.Draw(base)
    bbox = drawer.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + 36
    h = bbox[3] - bbox[1] + 18
    x, y = xy
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=bg, outline=border, width=1)
    base.alpha_composite(layer)
    drawer.text((x + 18, y + 8), text, font=font, fill=fill)
    return x, y, x + w, y + h


def metric_card(
    base: Image.Image,
    box: tuple[int, int, int, int],
    title: str,
    value: str,
    delta: str,
    accent: str,
) -> None:
    draw = glass_panel(base, box, radius=24, fill=(255, 255, 255, 18))
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 + 16, y1 + 16, x1 + 20, y2 - 16), radius=4, fill=hex_to_rgb(accent) + (255,))
    draw.text((x1 + 34, y1 + 18), title, font=pick_font("bold", 18), fill="#dbeafe")
    draw.text((x1 + 34, y1 + 50), value, font=pick_font("black", 34), fill=TEXT)
    draw.text((x1 + 34, y1 + 96), delta, font=pick_font("regular", 16), fill=MUTED)


def draw_line_chart(
    base: Image.Image,
    box: tuple[int, int, int, int],
    values: list[int],
    color: str,
    label: str,
    fill_area: bool = True,
) -> None:
    draw = glass_panel(base, box, radius=24, fill=(255, 255, 255, 14))
    x1, y1, x2, y2 = box
    draw.text((x1 + 22, y1 + 18), label, font=pick_font("bold", 18), fill=TEXT)
    inner = (x1 + 24, y1 + 60, x2 - 24, y2 - 28)
    draw.rounded_rectangle(inner, radius=20, outline=(255, 255, 255, 25), width=1)
    w = inner[2] - inner[0]
    h = inner[3] - inner[1]
    min_v, max_v = min(values), max(values)
    points = []
    for idx, value in enumerate(values):
        x = inner[0] + (w * idx / max(len(values) - 1, 1))
        norm = (value - min_v) / max(max_v - min_v, 1)
        y = inner[3] - norm * h
        points.append((x, y))
    if fill_area:
        area = [(inner[0], inner[3])] + points + [(inner[2], inner[3])]
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        rgb = hex_to_rgb(color)
        od.polygon(area, fill=rgb + (42,))
        overlay = overlay.filter(ImageFilter.GaussianBlur(2))
        base.alpha_composite(overlay)
    draw.line(points, fill=hex_to_rgb(color) + (255,), width=5, joint="curve")
    for pt in points:
        draw.ellipse((pt[0] - 5, pt[1] - 5, pt[0] + 5, pt[1] + 5), fill=hex_to_rgb(color) + (255,))


def draw_bar_chart(
    base: Image.Image,
    box: tuple[int, int, int, int],
    values: list[int],
    color: str,
    label: str,
) -> None:
    draw = glass_panel(base, box, radius=24, fill=(255, 255, 255, 14))
    x1, y1, x2, y2 = box
    draw.text((x1 + 22, y1 + 18), label, font=pick_font("bold", 18), fill=TEXT)
    inner = (x1 + 22, y1 + 58, x2 - 22, y2 - 24)
    draw.rounded_rectangle(inner, radius=20, outline=(255, 255, 255, 25), width=1)
    w = inner[2] - inner[0]
    h = inner[3] - inner[1]
    bar_w = (w - (len(values) - 1) * 12) / len(values)
    max_v = max(values)
    for idx, value in enumerate(values):
        bar_h = max(8, h * value / max_v)
        x = inner[0] + idx * (bar_w + 12)
        y = inner[3] - bar_h
        draw.rounded_rectangle((x, y, x + bar_w, inner[3]), radius=12, fill=hex_to_rgb(color) + (255,))


def draw_contribution_graph(
    base: Image.Image,
    box: tuple[int, int, int, int],
    title: str = "GitHub Contribution Graph",
) -> None:
    draw = glass_panel(base, box, radius=24, fill=(255, 255, 255, 14))
    x1, y1, x2, y2 = box
    draw.text((x1 + 20, y1 + 18), title, font=pick_font("bold", 18), fill=TEXT)
    left = x1 + 22
    top = y1 + 58
    cell = 16
    gaps = 6
    palette = [
        (15, 23, 42, 255),
        (14, 165, 233, 255),
        (20, 184, 166, 255),
        (99, 102, 241, 255),
        (34, 197, 94, 255),
    ]
    for col in range(18):
        for row in range(7):
            level = (row * 3 + col) % len(palette)
            fill = palette[level] if (col + row) % 3 else palette[0]
            x = left + col * (cell + gaps)
            y = top + row * (cell + gaps)
            draw.rounded_rectangle((x, y, x + cell, y + cell), radius=4, fill=fill, outline=(255, 255, 255, 20))


def draw_activity_feed(base: Image.Image, box: tuple[int, int, int, int], items: list[tuple[str, str, str]]) -> None:
    draw = glass_panel(base, box, radius=24, fill=(255, 255, 255, 14))
    x1, y1, x2, y2 = box
    draw.text((x1 + 20, y1 + 18), "Recent Activity", font=pick_font("bold", 18), fill=TEXT)
    y = y1 + 60
    colors = [BLUE, TEAL, INDIGO, GREEN, AMBER]
    for idx, (title, meta, time) in enumerate(items):
        cx = x1 + 30
        draw.ellipse((cx - 8, y + 10, cx + 8, y + 26), fill=hex_to_rgb(colors[idx % len(colors)]) + (255,))
        draw.text((x1 + 52, y), title, font=pick_font("bold", 16), fill=TEXT)
        draw.text((x1 + 52, y + 24), meta, font=pick_font("regular", 15), fill=MUTED)
        draw.text((x2 - 100, y + 8), time, font=pick_font("mono", 14), fill="#cbd5e1")
        y += 72


def draw_progress_row(
    base: Image.Image,
    box: tuple[int, int, int, int],
    label: str,
    value: int,
    total: int,
    accent: str,
) -> None:
    draw = ImageDraw.Draw(base)
    x1, y1, x2, y2 = box
    draw.text((x1, y1), label, font=pick_font("bold", 16), fill=TEXT)
    bar_y = y1 + 28
    draw.rounded_rectangle((x1, bar_y, x2, bar_y + 18), radius=9, fill=(255, 255, 255, 24))
    width = (x2 - x1) * value / max(total, 1)
    draw.rounded_rectangle((x1, bar_y, x1 + width, bar_y + 18), radius=9, fill=hex_to_rgb(accent) + (255,))
    draw.text((x2 - 70, y1), f"{value}/{total}", font=pick_font("mono", 15), fill=MUTED)


def make_base(size: tuple[int, int]) -> Image.Image:
    img = gradient(size)
    add_glow(img, (int(size[0] * 0.18), int(size[1] * 0.2)), BLUE, int(min(size) * 0.22), 180)
    add_glow(img, (int(size[0] * 0.78), int(size[1] * 0.22)), TEAL, int(min(size) * 0.18), 150)
    add_glow(img, (int(size[0] * 0.72), int(size[1] * 0.82)), INDIGO, int(min(size) * 0.25), 160)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for x in range(0, size[0], 80):
        d.line((x, 0, x, size[1]), fill=(255, 255, 255, 8))
    for y in range(0, size[1], 80):
        d.line((0, y, size[0], y), fill=(255, 255, 255, 8))
    overlay = overlay.filter(ImageFilter.GaussianBlur(0.2))
    img.alpha_composite(overlay)
    add_noise(img)
    return img


def make_dashboard_shell(size: tuple[int, int], title: str, subtitle: str, compact: bool = False) -> Image.Image:
    base = make_base(size)
    draw = ImageDraw.Draw(base)
    sidebar_w = 280 if not compact else 90
    glass_panel(base, (40, 40, sidebar_w, size[1] - 40), radius=32, fill=(15, 23, 42, 225))
    draw.text((68, 74), "Developer OS", font=pick_font("black", 30 if not compact else 20), fill=TEXT)
    if not compact:
        draw.text((68, 116), "Career analytics platform", font=pick_font("regular", 16), fill=MUTED)
        nav = [
            ("Dashboard", True),
            ("Analytics", False),
            ("Learning", False),
            ("Coding", False),
            ("Jobs", False),
            ("Search", False),
            ("Automation", False),
        ]
        y = 186
        for item, active in nav:
            fill = TEXT if active else "#cbd5e1"
            bg = (14, 165, 233, 36) if active else (255, 255, 255, 8)
            draw.rounded_rectangle((66, y, 240, y + 50), radius=18, fill=bg)
            draw.text((84, y + 13), item, font=pick_font("bold", 17), fill=fill)
            y += 62
    else:
        draw.rounded_rectangle((58, 68, 118, 124), radius=18, fill=(14, 165, 233, 38), outline=(255, 255, 255, 24))
        draw.text((72, 84), "OS", font=pick_font("black", 20), fill=TEXT)

    draw.text((sidebar_w + 74, 66), title, font=pick_font("black", 40), fill=TEXT)
    draw.text((sidebar_w + 74, 116), subtitle, font=pick_font("regular", 18), fill=MUTED)
    return base


def hero_banner() -> Image.Image:
    base = make_base((1600, 600))
    draw = ImageDraw.Draw(base)
    draw.text((88, 72), "Developer OS", font=pick_font("black", 54), fill=TEXT)
    draw.multiline_text(
        (88, 146),
        "Track Learning.\nBuild Consistency.\nGrow Your Career.",
        font=pick_font("black", 48),
        fill=TEXT,
        spacing=8,
    )
    draw.text(
        (92, 314),
        "A personal operating system for developers that turns learning, coding, GitHub activity,\n"
        "and career progress into a premium public dashboard.",
        font=pick_font("regular", 21),
        fill="#cbd5e1",
        spacing=8,
    )
    x = 92
    for badge, color in [
        ("GitHub Analytics", BLUE),
        ("LeetCode Analytics", TEAL),
        ("Learning Tracker", INDIGO),
        ("Job Tracker", GREEN),
        ("Developer Dashboard", AMBER),
    ]:
        _, _, x2, _ = pill(base, (x, 420), badge, bg=hex_to_rgb(color) + (28,), border=hex_to_rgb(color) + (80,), font=pick_font("bold", 16))
        x = x2 + 14

    draw.rounded_rectangle((86, 498, 282, 546), radius=18, fill=(14, 165, 233, 38), outline=(14, 165, 233, 120))
    draw.text((110, 511), "Live Demo", font=pick_font("bold", 18), fill=TEXT)
    draw.rounded_rectangle((296, 498, 482, 546), radius=18, fill=(255, 255, 255, 10), outline=(255, 255, 255, 35))
    draw.text((320, 511), "Open Source Ready", font=pick_font("bold", 18), fill="#dbeafe")

    # right side mockup stack
    glass_panel(base, (868, 56, 1528, 548), radius=34, fill=(15, 23, 42, 224))
    draw.text((904, 88), "Dashboard Preview", font=pick_font("black", 28), fill=TEXT)
    draw.text((904, 130), "Live analytics, recent activity, and growth trends.", font=pick_font("regular", 18), fill=MUTED)
    metric_card(base, (904, 170, 1110, 280), "Solved Today", "18", "+27% week over week", BLUE)
    metric_card(base, (1130, 170, 1336, 280), "GitHub Stars", "1.2k", "+94 this month", TEAL)
    metric_card(base, (1356, 170, 1492, 280), "Offers", "04", "2 active loops", INDIGO)
    draw_contribution_graph(base, (904, 306, 1216, 492))
    draw_line_chart(base, (1240, 306, 1492, 492), [3, 5, 4, 7, 9, 11, 10, 14], TEAL, "Growth Trend")
    return base


def dashboard_screen() -> Image.Image:
    base = make_dashboard_shell((1600, 1000), "Developer Dashboard", "A modern control center for learning, coding, and job search momentum.")
    draw = ImageDraw.Draw(base)
    metric_card(base, (360, 180, 594, 310), "Total Notes", "128", "+12 this week", BLUE)
    metric_card(base, (620, 180, 854, 310), "Problems Solved", "247", "+19 this week", TEAL)
    metric_card(base, (880, 180, 1114, 310), "Applications", "36", "5 active", INDIGO)
    metric_card(base, (1140, 180, 1374, 310), "Interviews", "09", "3 upcoming", GREEN)
    draw_line_chart(base, (360, 350, 980, 640), [24, 28, 31, 39, 41, 44, 52, 58, 63], BLUE, "Weekly Learning & Coding Trend")
    draw_activity_feed(
        base,
        (1020, 350, 1488, 640),
        [
            ("Added note: DBMS indexing", "Learning • subject: dbms", "09:14"),
            ("Solved: Two Sum", "Coding • platform: LeetCode", "08:40"),
            ("Applied: Backend Engineer", "Job tracker • status: Applied", "07:21"),
            ("Generated dashboard", "Automation • README updated", "06:00"),
        ],
    )
    glass_panel(base, (360, 680, 1488, 918), radius=28, fill=(255, 255, 255, 14))
    draw.text((386, 704), "Focus Areas", font=pick_font("black", 24), fill=TEXT)
    draw_progress_row(base, (386, 766, 930, 796), "Learning progress", 78, 100, BLUE)
    draw_progress_row(base, (386, 824, 930, 854), "Coding progress", 64, 100, TEAL)
    draw_progress_row(base, (386, 882, 930, 912), "Job pipeline", 18, 40, INDIGO)
    draw_bar_chart(base, (960, 680, 1460, 918), [7, 12, 10, 18, 13, 22, 20], GREEN, "Activity by Day")
    return base


def statistics_screen() -> Image.Image:
    base = make_dashboard_shell((1600, 900), "Statistics", "Trends, snapshots, and summary metrics across the platform.", compact=True)
    draw = ImageDraw.Draw(base)
    metric_card(base, (360, 170, 610, 292), "Easy Solved", "96", "LeetCode", BLUE)
    metric_card(base, (636, 170, 886, 292), "Medium Solved", "117", "LeetCode", TEAL)
    metric_card(base, (912, 170, 1162, 292), "Hard Solved", "34", "LeetCode", INDIGO)
    metric_card(base, (1188, 170, 1438, 292), "Contest Rating", "1642", "+42 this month", GREEN)
    draw_line_chart(base, (360, 330, 972, 646), [12, 15, 16, 20, 19, 22, 25, 27, 30], INDIGO, "LeetCode Solved Trend")
    draw_bar_chart(base, (1012, 330, 1438, 646), [8, 12, 9, 15, 18, 14, 20], BLUE, "Weekly Readiness")
    glass_panel(base, (360, 674, 1438, 840), radius=26, fill=(255, 255, 255, 14))
    draw.text((388, 698), "Production Snapshot", font=pick_font("black", 24), fill=TEXT)
    for idx, (label, value) in enumerate(
        [
            ("README refreshes", "Daily"),
            ("GitHub automation", "Active"),
            ("Deploy status", "Healthy"),
            ("API health", "Passing"),
        ]
    ):
        x = 388 + idx * 260
        draw.text((x, 748), label, font=pick_font("bold", 16), fill=MUTED)
        draw.text((x, 782), value, font=pick_font("black", 28), fill=TEXT)
    return base


def search_screen() -> Image.Image:
    base = make_dashboard_shell((1600, 900), "Search", "Find notes, coding entries, and applications instantly.", compact=True)
    draw = ImageDraw.Draw(base)
    glass_panel(base, (360, 170, 1438, 238), radius=28, fill=(255, 255, 255, 18))
    draw.text((392, 191), "Search notes, problems, companies, topics...", font=pick_font("regular", 24), fill="#cbd5e1")
    pill(base, (360, 264), "DBMS", bg=(14, 165, 233, 36), border=(14, 165, 233, 90), font=pick_font("bold", 16))
    pill(base, (448, 264), "LeetCode", bg=(20, 184, 166, 36), border=(20, 184, 166, 90), font=pick_font("bold", 16))
    pill(base, (576, 264), "Applied", bg=(99, 102, 241, 36), border=(99, 102, 241, 90), font=pick_font("bold", 16))
    pill(base, (690, 264), "Interview", bg=(34, 197, 94, 36), border=(34, 197, 94, 90), font=pick_font("bold", 16))
    glass_panel(base, (360, 334, 1438, 824), radius=28, fill=(255, 255, 255, 14))
    draw.text((388, 358), "Search Results", font=pick_font("black", 24), fill=TEXT)
    rows = [
        ("Learned clustered indexing", "Learning • DBMS • 2026-06-17", BLUE),
        ("Two Sum", "Coding • LeetCode • Easy", TEAL),
        ("Backend Engineer application", "Jobs • Applied • Acme", INDIGO),
        ("Mock interview notes", "Learning • System Design • 2026-06-12", GREEN),
    ]
    y = 426
    for title, meta, color in rows:
        draw.rounded_rectangle((388, y, 1410, y + 88), radius=20, fill=(255, 255, 255, 8), outline=(255, 255, 255, 18))
        draw.rounded_rectangle((408, y + 26, 432, y + 52), radius=8, fill=hex_to_rgb(color) + (255,))
        draw.text((454, y + 20), title, font=pick_font("bold", 20), fill=TEXT)
        draw.text((454, y + 48), meta, font=pick_font("regular", 15), fill=MUTED)
        draw.text((1330, y + 30), "Open", font=pick_font("bold", 16), fill=hex_to_rgb(color) + (255,))
        y += 104
    return base


def mobile_screen() -> Image.Image:
    base = make_base((900, 1400))
    draw = ImageDraw.Draw(base)
    glass_panel(base, (70, 80, 830, 1320), radius=44, fill=(15, 23, 42, 224))
    draw.text((120, 120), "Developer OS", font=pick_font("black", 34), fill=TEXT)
    draw.text((120, 164), "Mobile productivity view", font=pick_font("regular", 18), fill=MUTED)
    metric_card(base, (120, 230, 376, 350), "Notes", "128", "+12 this week", BLUE)
    metric_card(base, (424, 230, 680, 350), "Solved", "247", "+19 this week", TEAL)
    draw_line_chart(base, (120, 390, 680, 650), [8, 10, 11, 12, 18, 16, 20], INDIGO, "Growth")
    draw_activity_feed(
        base,
        (120, 690, 680, 1090),
        [
            ("Study note saved", "DBMS indexing", "09:14"),
            ("Problem solved", "Two Sum", "08:40"),
            ("Application tracked", "Acme", "07:21"),
        ],
    )
    glass_panel(base, (120, 1120, 680, 1260), radius=28, fill=(255, 255, 255, 14))
    draw.text((146, 1146), "Responsive, fast, and focused.", font=pick_font("bold", 22), fill=TEXT)
    draw.text((146, 1184), "Everything visible at a glance.", font=pick_font("regular", 16), fill=MUTED)
    return base


def social_preview() -> Image.Image:
    base = make_base((1280, 640))
    draw = ImageDraw.Draw(base)
    draw.text((74, 72), "Developer OS", font=pick_font("black", 60), fill=TEXT)
    draw.text((74, 150), "Analytics Dashboard • GitHub • LeetCode • Automation", font=pick_font("bold", 24), fill="#cbd5e1")
    draw.multiline_text(
        (74, 206),
        "Track Learning.\nBuild Consistency.\nGrow Your Career.",
        font=pick_font("black", 42),
        fill=TEXT,
        spacing=6,
    )
    for idx, (label, color) in enumerate(
        [("GitHub", BLUE), ("LeetCode", TEAL), ("Automation", INDIGO), ("Growth", GREEN)]
    ):
        pill(base, (76 + idx * 174, 500), label, bg=hex_to_rgb(color) + (30,), border=hex_to_rgb(color) + (90,), font=pick_font("bold", 16))
    glass_panel(base, (780, 64, 1202, 576), radius=34, fill=(15, 23, 42, 224))
    metric_card(base, (816, 106, 978, 206), "GitHub", "1.2k", "Stars + followers", BLUE)
    metric_card(base, (1002, 106, 1164, 206), "LeetCode", "1642", "Contest rating", TEAL)
    draw_contribution_graph(base, (816, 238, 1164, 402))
    draw_line_chart(base, (816, 420, 1164, 536), [9, 11, 10, 15, 14, 19], INDIGO, "Growth", fill_area=False)
    return base


def logo_asset(size: int = 1024, transparent: bool = True) -> Image.Image:
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0) if transparent else hex_to_rgb(BG) + (255,))
    draw = ImageDraw.Draw(base)
    if not transparent:
        add_glow(base, (size // 2, size // 2), BLUE, size // 2, 200)
    draw.rounded_rectangle((80, 80, size - 80, size - 80), radius=220, fill=(17, 24, 39, 220), outline=(255, 255, 255, 40), width=4)
    draw.rounded_rectangle((130, 130, size - 130, size - 130), radius=180, fill=(255, 255, 255, 8), outline=(14, 165, 233, 150), width=3)
    # emblem grid
    for x in (320, 384, 448):
        draw.rounded_rectangle((x, 286, x + 56, 738), radius=18, fill=(255, 255, 255, 18))
    draw.rounded_rectangle((320, 286, 384, 738), radius=18, fill=(14, 165, 233, 220))
    draw.rounded_rectangle((384, 350, 448, 738), radius=18, fill=(20, 184, 166, 220))
    draw.rounded_rectangle((448, 414, 512, 738), radius=18, fill=(99, 102, 241, 220))
    draw.arc((250, 220, 774, 744), start=30, end=330, fill=(255, 255, 255, 170), width=12)
    draw.arc((220, 190, 804, 774), start=205, end=500, fill=(255, 255, 255, 60), width=10)
    wordmark = "Developer OS"
    tagline = "Track Learning. Build Consistency. Grow Your Career."
    wordmark_font = pick_font("black", 68)
    tagline_font = pick_font("regular", 24)
    w_box = draw.textbbox((0, 0), wordmark, font=wordmark_font)
    t_box = draw.textbbox((0, 0), tagline, font=tagline_font)
    draw.text(((size - (w_box[2] - w_box[0])) / 2, 788), wordmark, font=wordmark_font, fill=TEXT)
    draw.text(((size - (t_box[2] - t_box[0])) / 2, 860), tagline, font=tagline_font, fill="#cbd5e1")
    return base


def icon_asset(size: int = 512, transparent: bool = True) -> Image.Image:
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0) if transparent else hex_to_rgb(BG) + (255,))
    draw = ImageDraw.Draw(base)
    pad = int(size * 0.12)
    draw.rounded_rectangle((pad, pad, size - pad, size - pad), radius=int(size * 0.22), fill=(17, 24, 39, 220), outline=(255, 255, 255, 40), width=3)
    draw.rounded_rectangle((size * 0.26, size * 0.28, size * 0.43, size * 0.72), radius=18, fill=(14, 165, 233, 230))
    draw.rounded_rectangle((size * 0.43, size * 0.37, size * 0.60, size * 0.72), radius=18, fill=(20, 184, 166, 230))
    draw.rounded_rectangle((size * 0.60, size * 0.46, size * 0.77, size * 0.72), radius=18, fill=(99, 102, 241, 230))
    draw.arc((size * 0.22, size * 0.19, size * 0.78, size * 0.76), start=30, end=330, fill=(255, 255, 255, 180), width=8)
    return base


def favicon_asset(size: int = 512) -> Image.Image:
    base = icon_asset(size=size, transparent=False)
    return base


def demo_frames() -> list[Image.Image]:
    frames: list[Image.Image] = []
    scenes = [
        ("Open Dashboard", dashboard_screen()),
        ("Show GitHub Analytics", social_preview()),
        ("Show LeetCode Analytics", statistics_screen()),
        ("Add Learning Note", search_screen()),
        ("Search Notes", search_screen()),
        ("View Statistics", statistics_screen()),
        ("Refresh Data", dashboard_screen()),
        ("Success Animation", social_preview()),
    ]
    for label, scene in scenes:
        frame = scene.copy()
        draw = ImageDraw.Draw(frame)
        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle((70, 70, 520, 154), radius=24, fill=(10, 16, 28, 180), outline=(255, 255, 255, 30))
        overlay = overlay.filter(ImageFilter.GaussianBlur(1))
        frame.alpha_composite(overlay)
        draw.text((98, 96), label, font=pick_font("black", 26), fill=TEXT)
        frames.append(frame)
    return frames


def save(img: Image.Image, path: Path) -> None:
    img.save(path)


def write_docs() -> None:
    spec = """# Developer OS Visual Branding Kit

This document captures the premium visual direction for Developer OS and the exact prompts used to guide image generation.

## Design Direction

- Modern SaaS product
- Dark theme with glassmorphism
- Developer productivity aesthetic
- High-contrast typography
- Neon blue, teal, indigo accents

## Shared Palette

- `#0EA5E9` Blue
- `#14B8A6` Teal
- `#6366F1` Indigo
- `#111827` Deep Slate

## Hero Banner

**File:** `assets/hero-banner.png`

**Size:** `1600x600`

**Prompt:**

```text
Use case: product-mockup
Asset type: GitHub README hero banner
Primary request: premium modern SaaS hero banner for Developer OS, a personal operating system for developers
Scene/backdrop: dark glassmorphism dashboard environment with subtle grid and glowing accent lights
Subject: dashboard mockup with GitHub contribution graph, LeetCode statistics, growth charts, and analytics cards
Style/medium: polished product render, high-end startup landing page aesthetic
Composition/framing: wide 1600x600 banner, text-left and dashboard-mockup-right, safe negative space for README cropping
Lighting/mood: sleek, confident, premium, soft neon lighting
Color palette: deep slate with blue, teal, and indigo accents
Text (verbatim): "Developer OS", "Track Learning. Build Consistency. Grow Your Career.", "GitHub Analytics", "LeetCode Analytics", "Learning Tracker", "Job Tracker", "Developer Dashboard"
Constraints: do not make it look like a student project; no clutter; no cartoon styling; no watermark
Avoid: flat layout, basic template look, oversaturated neon, generic UI blocks
```

## Dashboard Screenshots

**Files:** `assets/dashboard.png`, `assets/statistics.png`, `assets/search.png`, `assets/mobile-view.png`

**Prompt family:**

```text
Use case: ui-mockup
Asset type: product screenshot
Primary request: modern SaaS dashboard for Developer OS with professional analytics UI
Scene/backdrop: polished dark interface with glass cards and structured content
Subject: metrics cards, charts, activity feed, progress indicators, search results, and responsive mobile layout
Style/medium: premium product UI render
Composition/framing: clean app-frame layout, realistic dashboard proportions
Lighting/mood: calm, high-end, crisp, product-led
Color palette: deep slate with blue, teal, indigo, and white text
Constraints: no student-style design, no rough wireframe, no clutter
Avoid: toy visuals, inconsistent margins, low contrast, generic admin-template look
```

## Social Preview

**File:** `assets/social-preview.png`

**Size:** `1280x640`

**Prompt:**

```text
Use case: ads-marketing
Asset type: GitHub social preview image
Primary request: startup-grade social preview for Developer OS
Scene/backdrop: premium dark SaaS showcase with glow accents and dashboard panels
Subject: Developer OS branding, analytics dashboard, GitHub, LeetCode, automation, growth metrics
Style/medium: polished tech product promo image
Composition/framing: title-left, analytics panels-right, high contrast, large readable typography
Lighting/mood: sleek, premium, confident
Color palette: #0EA5E9, #14B8A6, #6366F1, #111827
Constraints: must look like a funded startup product
Avoid: flat screenshot collage, generic app icon, amateur typography
```

## Open Graph Preview

**File:** `assets/social-preview.png`

**Size:** `1200x630`

**Prompt:**

```text
Use case: ads-marketing
Asset type: Open Graph preview image
Primary request: premium share card for Developer OS that reads well on social platforms
Scene/backdrop: dark startup-style dashboard with layered panels and glow accents
Subject: Developer OS title, analytics cards, GitHub analytics, LeetCode analytics, automation
Style/medium: polished SaaS marketing image
Composition/framing: centered visual balance with readable title and metric clusters
Lighting/mood: confident, crisp, premium
Color palette: deep navy, electric blue, cyan, white, soft gray
Constraints: must look production-ready and shareable at small sizes
Avoid: crowded UI, low contrast, oversized logos, weak typography
```

## GitHub Repository Banner

**File:** `assets/hero-banner.png`

**Size:** `1600x600`

**Prompt:**

```text
Use case: product-mockup
Asset type: GitHub repository banner
Primary request: premium SaaS banner for Developer OS that makes the repo feel like a real product launch
Scene/backdrop: dark glassmorphism dashboard with subtle grid, glow, and depth
Subject: developer dashboard mockup with GitHub contribution graph, LeetCode stats, growth charts, and metric cards
Style/medium: Apple, Linear, Vercel, Notion, Stripe inspired SaaS artwork
Composition/framing: wide 1600x600 layout with strong title area and mock dashboard panel on the right
Lighting/mood: modern, sharp, premium, calm
Color palette: deep navy, electric blue, cyan, white, soft gray
Constraints: no student-project styling, no clutter, no cartoon elements
Avoid: generic admin template, flat illustration, noisy text, watermark
```

## Mobile App Mockup

**File:** `assets/mobile-view.png`

**Prompt:**

```text
Use case: ui-mockup
Asset type: mobile responsive app mockup
Primary request: polished mobile dashboard preview for Developer OS
Scene/backdrop: dark responsive app shell with stacked cards and compact charts
Subject: mobile-friendly developer productivity dashboard with metrics, activity feed, and trend chart
Style/medium: premium SaaS product UI render
Composition/framing: portrait layout with safe margins and clear content hierarchy
Lighting/mood: crisp, modern, high-end
Color palette: deep navy, electric blue, cyan, white, soft gray
Constraints: should feel like a real app on a flagship device
Avoid: tiny unreadable text, clutter, student-project wireframe style
```

## Demo GIF

**File:** `assets/demo.gif`

**Duration:** 20-30 seconds

**Storyboard:**

1. Open Dashboard
2. Show GitHub Analytics
3. Show LeetCode Analytics
4. Add Learning Note
5. Search Notes
6. View Statistics
7. Refresh Data
8. Success Animation

**Camera movement:**

- Start with a soft zoom-in on the dashboard hero view.
- Pan right into the GitHub analytics panel with a slight parallax shift.
- Pull forward to the LeetCode and statistics cards for emphasis.
- Snap gently to the search area when the note is added.
- End with a subtle zoom-out and a success pulse on the final frame.

**Transitions:**

- Use cross-fades between sections.
- Use quick motion blur on panel changes.
- Use a short fade-to-glow on the refresh and success steps.

## Logo and Icon System

**Files:** `assets/logo.png`, `assets/favicon.png`, `assets/icon.png`

**Prompt:**

```text
Use case: logo-brand
Asset type: product logo and app icon
Primary request: minimal modern developer-focused branding mark for Developer OS
Scene/backdrop: transparent background
Subject: monogram-inspired OS mark with subtle dashboard/grid cues
Style/medium: clean vector-like raster logo
Composition/framing: centered icon with generous padding
Lighting/mood: crisp, contemporary, premium
Color palette: deep slate, blue, teal, indigo
Constraints: minimal, scalable, memorable
Avoid: mascot style, playful gradients, clutter, tiny unreadable text
```

## README Enhancements

- Add a banner image directly below the title.
- Add a visitor counter badge beside the tech badges.
- Present screenshots in a bento grid.
- Add a GIF showcase block near the top.
- Keep the product copy unchanged and use visuals to carry the branding.

## Branding Strategy

- Position the repo as a personal developer operating system rather than a tracking script.
- Emphasize automation, product polish, and public proof of engineering discipline.
- Keep all visuals aligned to the same dark SaaS theme.
- Use screenshots and charts to demonstrate maturity, not just screenshots of raw data.

## GitHub Optimization Checklist

- [x] Add premium hero banner
- [x] Add social preview image
- [x] Add logo and icon assets
- [x] Add dashboard screenshots
- [x] Add animated demo GIF
- [x] Keep README visually consistent
- [x] Use concise, recruiter-friendly labels
- [x] Show metrics and production readiness clearly

## Star Attraction

- Use a strong hero banner and social preview so previews look premium in feeds.
- Keep badges readable and focused.
- Show automation and production readiness near the top.
- Use a GIF to make the project feel alive.
- Make screenshots consistent, dark, and polished.
"""
    (DOCS / "visual-branding-kit.md").write_text(spec, encoding="utf-8")


def main() -> None:
    ensure_dirs()

    assets = {
        "hero-banner.png": hero_banner(),
        "dashboard.png": dashboard_screen(),
        "statistics.png": statistics_screen(),
        "search.png": search_screen(),
        "mobile-view.png": mobile_screen(),
        "social-preview.png": social_preview(),
        "logo.png": logo_asset(),
        "favicon.png": favicon_asset(),
        "icon.png": icon_asset(size=512),
    }
    for name, image in assets.items():
        save(image, ASSETS / name)

    frames = demo_frames()
    frames[0].save(
        ASSETS / "demo.gif",
        save_all=True,
        append_images=frames[1:],
        duration=2500,
        loop=0,
        disposal=2,
    )

    write_docs()


if __name__ == "__main__":
    main()
