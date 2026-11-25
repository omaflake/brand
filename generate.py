#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generates the omaflake brand kit: master SVGs, PNG exports, .icns, favicon.ico, the web head files, the NixOS
guests' loading screen (plymouth/) and desktop wallpapers for the guests (wallpapers/). copy.py copies what the other repositories use into their checkouts.

Needs Python 3.11+ (tomllib), rsvg-convert (Homebrew: librsvg) and iconutil (macOS). Run from anywhere:
    python3 generate.py
"""
import os, random, shutil, struct, subprocess, tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
SVG, PNG = os.path.join(HERE, "svg"), os.path.join(HERE, "png")

# The palette (palette.toml) – omaflake's design tokens carry a copy of it
with open(os.path.join(HERE, "palette.toml"), "rb") as f:
    _P = tomllib.load(f)["palette"]
BG = _P["background"]   # icon background
RED, CYAN, YELLOW, WHITE = _P["red"], _P["cyan"], _P["yellow"], _P["white"]
TILT = 14               # rotation of the hero flake in degrees


def svg(view_box, body, size=None):
    vb_w, vb_h = (float(n) for n in view_box.split()[2:])
    w, h = size, round(size * vb_h / vb_w) if size else None
    dims = f' width="{w}" height="{h}"' if size else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}"{dims}>\n{body}\n</svg>\n'


def six(ref, cx=512, cy=512, attrs=""):
    return "".join(f'<use href="#{ref}" transform="rotate({a} {cx} {cy})"{attrs}/>' for a in range(0, 360, 60))


# --- chaotic hero ---------------------------------------------------------------------------

ARM = ('<line x1="512" y1="440" x2="512" y2="230"/>'
       '<polyline points="446,356 512,296 578,356"/><polyline points="470,262 512,224 554,262"/>')


def hero_defs(p):
    """Defs for the chaotic flake; p is an id prefix so several can share one document."""
    return (f'<g id="{p}arm" fill="none" stroke-width="30" stroke-linecap="round" stroke-linejoin="round">{ARM}</g>'
            f'<g id="{p}flake">{six(p + "arm")}</g>'
            f'<mask id="{p}bands" maskUnits="userSpaceOnUse" x="-2000" y="-2000" width="5000" height="5000">'
            f'<rect x="-2000" y="-2000" width="5000" height="5000" fill="#fff"/>'
            f'<rect x="-2000" y="470" width="5000" height="22" fill="#000"/>'
            f'<rect x="-2000" y="600" width="5000" height="10" fill="#000"/></mask>')


def hero_flake(p, core=WHITE):
    """RGB-split flake with glitch bands cut out."""
    t = f"rotate({TILT} 512 512)"
    return (f'<g mask="url(#{p}bands)">'
            f'<use href="#{p}flake" stroke="{RED}" transform="translate(-16 6) {t}" opacity="0.85"/>'
            f'<use href="#{p}flake" stroke="{CYAN}" transform="translate(16 -6) {t}" opacity="0.85"/>'
            f'<use href="#{p}flake" stroke="{core}" transform="{t}"/></g>')


def hero_noise(p):
    """Scattered pixels and mini flakes around the hero."""
    rnd = random.Random(7)
    pixels = "".join(
        f'<rect x="{rnd.randint(120, 880)}" y="{rnd.randint(120, 880)}" width="{rnd.choice([10, 18, 26])}" '
        f'height="{rnd.choice([10, 18])}" fill="{rnd.choice([RED, CYAN, WHITE, YELLOW])}" opacity="{rnd.choice([0.5, 0.8, 1])}"/>'
        for _ in range(40))
    minis = "".join(
        f'<use href="#{p}flake" transform="translate({x} {y}) scale({s}) rotate({r} 512 512)" stroke="{c}" opacity="0.7"/>'
        for x, y, s, r, c in [(130, 120, .22, 20, YELLOW), (690, 170, .18, -12, CYAN), (150, 690, .2, 33, RED),
                              (720, 700, .16, 5, WHITE), (600, 90, .12, 40, RED)])
    return f'<g mask="url(#{p}bands)">{pixels}{minis}</g>'


def hero_scene(p):
    return hero_noise(p) + hero_flake(p)


# macOS icon grid: 824x824 rounded square centred on a 1024 canvas
ICON_RECT = 'x="100" y="100" width="824" height="824" rx="185"'


def app_icon():
    return svg("0 0 1024 1024",
               f'<defs>{hero_defs("h-")}<clipPath id="clip"><rect {ICON_RECT}/></clipPath></defs>'
               f'<rect {ICON_RECT} fill="{BG}"/><g clip-path="url(#clip)">{hero_scene("h-")}</g>', 1024)


def fullbleed():
    """Square, edge to edge: GitHub avatar, social, PWA, apple-touch-icon."""
    return svg("100 100 824 824",
               f'<defs>{hero_defs("h-")}</defs><rect x="100" y="100" width="824" height="824" fill="{BG}"/>{hero_scene("h-")}',
               1024)


MARK_BOX = "150 150 724 724"


def mark(core):
    """The hero flake alone, transparent background."""
    return svg(MARK_BOX, f'<defs>{hero_defs("h-")}</defs>{hero_flake("h-", core)}', 1024)


# --- glyph: the hero flake, one colour, no split, no bands ------------------------------------

# Full glyph: exactly the hero's arm and tilt, for 64 px and up.
GLYPH_BOX = MARK_BOX


def glyph_body(p, color, width=34):
    return (f'<defs><g id="{p}arm" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
            f'stroke-linejoin="round">{ARM}</g></defs><g transform="rotate({TILT} 512 512)">{six(p + "arm")}</g>')


def glyph(color):
    return svg(GLYPH_BOX, glyph_body("g-", color), 1024)


# Small glyph: same tilt and open core, but one wide chevron per arm and a heavy stroke,
# so it stays readable at 16-18 px (menu bar, favicon).
SMALL_ARM = '<line x1="512" y1="424" x2="512" y2="250"/><polyline points="446,316 512,250 578,316"/>'
SMALL_BOX = "206 206 612 612"


def small_body(p, color, width=60):
    return (f'<defs><g id="{p}arm" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
            f'stroke-linejoin="round">{SMALL_ARM}</g></defs><g transform="rotate({TILT} 512 512)">{six(p + "arm")}</g>')


def menubar():
    """Template image: black on transparent, macOS tints it for light/dark."""
    return svg(SMALL_BOX, small_body("m-", "#000"), 18)


def glyph_small(color):
    return svg(SMALL_BOX, small_body("s-", color), 1024)


def favicon():
    """Transparent; dark flake on light browser chrome, light flake on dark (SVG only)."""
    return svg(SMALL_BOX,
               f'<style>.f{{color:{BG}}} @media (prefers-color-scheme: dark){{.f{{color:{WHITE}}}}}</style>'
               f'<g class="f">{small_body("f-", "currentColor")}</g>', 32)


def app_icon_small():
    """App icon for the 16 and 32 px slots: small glyph on the icon background."""
    return svg("0 0 1024 1024",
               f'<rect {ICON_RECT} fill="{BG}"/>'
               f'<g transform="translate(512 512) scale(1.25) translate(-512 -512)">{small_body("s-", WHITE)}</g>', 1024)


def social():
    rnd = random.Random(11)
    pixels = "".join(
        f'<rect x="{rnd.randint(0, 1270)}" y="{rnd.randint(0, 630)}" width="{rnd.choice([8, 14, 20])}" height="{rnd.choice([8, 14])}" '
        f'fill="{rnd.choice([RED, CYAN, WHITE, YELLOW])}" opacity="{rnd.choice([0.3, 0.6, 0.9])}"/>' for _ in range(70))
    word = 'font-family="Menlo, monospace" font-weight="bold" font-size="128"'
    tag = 'font-family="Menlo, monospace" font-size="27" fill="#B8C0CC"'
    return svg("0 0 1280 640",
               f'<defs>{hero_defs("h-")}</defs><rect width="1280" height="640" fill="{BG}"/>{pixels}'
               f'<g transform="translate(270 320) scale(0.62) translate(-512 -512)">{hero_flake("h-")}</g>'
               f'<text x="526" y="320" {word} fill="{RED}" opacity="0.85">omaflake</text>'
               f'<text x="546" y="312" {word} fill="{CYAN}" opacity="0.85">omaflake</text>'
               f'<text x="536" y="316" {word} fill="{WHITE}">omaflake</text>'
               f'<text x="540" y="392" {tag}>Opinionated, disposable NixOS and</text>'
               f'<text x="540" y="430" {tag}>macOS VMs on Mac and Linux.</text>', 1280)


# --- loading screen: NixOS guests' Plymouth theme and QEMU's window until it shows ----------
#
# One layout in units of the screen's height H (16:9): the hero flake LOAD_FLAKE·H wide, centred at LOAD_CY·H, the
# word mark under it, the bar near the bottom. The Plymouth script (nix/modules/plymouth/omaflake.script) places the
# same pieces at the same places and animates them; QEMU shows loading.png – that script's first frame – from the
# window's start until the guest's Plymouth draws, so the hand-over does not jump.

LOAD_W, LOAD_H = 2560, 1440
LOAD_FLAKE, LOAD_CY = 0.40, 0.44     # flake width and centre, of H (the flake's box is MARK_BOX, 724 units)
LOAD_WORD, LOAD_WORD_Y = 0.30, 0.71  # word mark width and centre, of H
WORD_BOX = (1180, 230)               # the word mark's own canvas


def load_pixels(w, h):
    """Pixels spread over the whole screen, fewer around the flake."""
    rnd = random.Random(23)
    out = []
    while len(out) < 150:
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if ((x - w / 2) / (0.26 * w)) ** 2 + ((y - LOAD_CY * h) / (0.42 * h)) ** 2 < 1:
            continue
        u = h / 640
        out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{rnd.choice([8, 14, 20]) * u:.0f}" '
                   f'height="{rnd.choice([8, 14]) * u:.0f}" fill="{rnd.choice([RED, CYAN, WHITE, YELLOW])}" '
                   f'opacity="{rnd.choice([0.25, 0.45, 0.7])}"/>')
    return "".join(out)


def load_background():
    return svg(f"0 0 {LOAD_W} {LOAD_H}", f'<rect width="{LOAD_W}" height="{LOAD_H}" fill="{BG}"/>'
               + load_pixels(LOAD_W, LOAD_H), LOAD_W)


def load_layer(color, opacity):
    """One colour of the hero flake, centred, no offset: the script moves red and cyan apart."""
    return svg(MARK_BOX, f'<defs>{hero_defs("h-")}</defs><g mask="url(#h-bands)">'
               f'<use href="#h-flake" stroke="{color}" transform="rotate({TILT} 512 512)" opacity="{opacity}"/></g>', 1024)


def load_mini(color, angle):
    return svg(MARK_BOX, f'<defs>{hero_defs("h-")}</defs>'
               f'<use href="#h-flake" stroke="{color}" transform="rotate({angle} 512 512)"/>', 256)


def load_word():
    w, h = WORD_BOX
    word = 'font-family="Menlo, monospace" font-weight="bold" font-size="200" text-anchor="middle"'
    return svg(f"0 0 {w} {h}",
               f'<text x="{w / 2 - 10}" y="184" {word} fill="{RED}" opacity="0.85">omaflake</text>'
               f'<text x="{w / 2 + 10}" y="176" {word} fill="{CYAN}" opacity="0.85">omaflake</text>'
               f'<text x="{w / 2}" y="180" {word} fill="{WHITE}">omaflake</text>', w)


def load_frame():
    """The script's first frame: background, the flake with its usual split, the word mark."""
    s = LOAD_FLAKE * LOAD_H / 724          # MARK_BOX units → pixels
    cx, cy = LOAD_W / 2, LOAD_CY * LOAD_H
    ww = LOAD_WORD * LOAD_H
    wh = ww * WORD_BOX[1] / WORD_BOX[0]
    flake = (f'<g transform="translate({cx} {cy}) scale({s}) translate(-512 -512)">{hero_flake("h-")}</g>')
    word = load_word().split("\n", 1)[1].rsplit("</svg>", 1)[0]
    return svg(f"0 0 {LOAD_W} {LOAD_H}",
               f'<defs>{hero_defs("h-")}</defs><rect width="{LOAD_W}" height="{LOAD_H}" fill="{BG}"/>'
               + load_pixels(LOAD_W, LOAD_H) + flake
               + f'<g transform="translate({cx - ww / 2} {LOAD_WORD_Y * LOAD_H - wh / 2}) scale({ww / WORD_BOX[0]})">'
               f'{word}</g>', LOAD_W)


def loading_screen(theme, qemu_png):
    """Writes the Plymouth theme's images and constants, and QEMU's loading image."""
    tmp = os.path.join(SVG, "loading")
    parts = {"background": (load_background(), LOAD_W, LOAD_H), "frame": (load_frame(), LOAD_W, LOAD_H),
             "flake-red": (load_layer(RED, 0.85), 1024, None), "flake-cyan": (load_layer(CYAN, 0.85), 1024, None),
             "flake-white": (load_layer(WHITE, 1), 1024, None), "word": (load_word(), *WORD_BOX)}
    for i, (c, a) in enumerate([(RED, 20), (CYAN, -12), (YELLOW, 33), (WHITE, 5), (RED, 47), (CYAN, 28)]):
        parts[f"mini-{i}"] = (load_mini(c, a), 192, None)
    for name, (content, w, h) in parts.items():
        write(f"{tmp}/{name}.svg", content)
        out = qemu_png if name == "frame" else f"{theme}/{name}.png"
        render(f"{tmp}/{name}.svg", out, w, h)
    # The bar: a track and its fill, 4 px squares the script stretches
    for name, colour, alpha in (("bar-track", WHITE, 0.12), ("bar-fill", CYAN, 1)):
        write(f"{tmp}/{name}.svg", svg("0 0 4 4", f'<rect width="4" height="4" fill="{colour}" fill-opacity="{alpha}"/>', 4))
        render(f"{tmp}/{name}.svg", f"{theme}/{name}.png", 4)
    write(f"{theme}/layout.script",
          "# Generated by omaflake/brand (generate.py) – do not edit. The layout, in units of the screen's height.\n"
          f"layout.flake = {LOAD_FLAKE};\nlayout.cy = {LOAD_CY};\nlayout.word = {LOAD_WORD};\n"
          f"layout.word_y = {LOAD_WORD_Y};\nlayout.word_aspect = {WORD_BOX[1] / WORD_BOX[0]:.4f};\n"
          f"layout.minis = {6};\n"
          # The red and cyan layers' offset in hero_flake, in MARK_BOX units
          "layout.split_x = 16 / 724;\nlayout.split_y = 6 / 724;\n")


# --- desktop wallpapers for the guests -------------------------------------------------------
#
# Five motifs, each in 16:9 and 16:10. Laid out in units of the screen's height (u = 1/1080 of H) and fractions of
# its width, so both shapes show the same picture. Flat shapes only – no gradients or blur – so the PNGs stay small.

WALL_SIZES = ((3840, 2160), (3840, 2400))


def placed(body, cx, cy, size):
    """body drawn in the 1024 space, its flake (MARK_BOX, 724 units wide) centred at cx, cy and size px wide."""
    return f'<g transform="translate({cx:.1f} {cy:.1f}) scale({size / 724:.5f}) translate(-512 -512)">{body}</g>'


def wall_pixels(rnd, w, h, n, keep_out=None, opacity=(0.25, 0.45, 0.7)):
    """Scattered pixels; keep_out = (cx, cy, rx, ry), an ellipse left empty."""
    u, out = h / 1080, []
    while len(out) < n:
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if keep_out and ((x - keep_out[0]) / keep_out[2]) ** 2 + ((y - keep_out[1]) / keep_out[3]) ** 2 < 1:
            continue
        out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{rnd.choice([8, 14, 20]) * u:.0f}" '
                   f'height="{rnd.choice([8, 14]) * u:.0f}" fill="{rnd.choice([RED, CYAN, WHITE, YELLOW])}" '
                   f'opacity="{rnd.choice(opacity)}"/>')
    return "".join(out)


def wall_glitch(w, h):
    """The hero, big and centred, with slices of it pushed sideways and pixels all over the screen."""
    rnd, u = random.Random(31), h / 1080
    cx, cy, size = w / 2, h / 2, 0.66 * h
    s = size / 724
    hero = placed(hero_flake("h-"), cx, cy, size)
    # Slices: a strip of the screen showing the flake again, shifted – the hero's bands, writ large
    slices, clips = "", ""
    for i, (y0, hh, dx) in enumerate([(-0.20, 0.035, 46), (0.09, 0.012, -54), (0.17, 0.05, 30)]):
        clips += f'<clipPath id="s{i}"><rect x="0" y="{cy + y0 * h:.0f}" width="{w}" height="{hh * h:.0f}"/></clipPath>'
        slices += (f'<g clip-path="url(#s{i})"><rect x="0" y="{cy + y0 * h:.0f}" width="{w}" height="{hh * h:.0f}" '
                   f'fill="{BG}"/><g transform="translate({dx * u:.0f} 0)">{hero}</g></g>')
    lines = "".join(f'<rect x="{x * w:.0f}" y="{y * h:.0f}" width="{l * w:.0f}" height="{t * u:.0f}" fill="{c}" '
                    f'opacity="{o}"/>' for x, y, l, t, c, o in
                    [(0.00, 0.21, 0.31, 4, CYAN, 0.6), (0.66, 0.36, 0.34, 3, RED, 0.6), (0.08, 0.74, 0.22, 6, RED, 0.45),
                     (0.71, 0.81, 0.29, 4, CYAN, 0.5), (0.40, 0.93, 0.20, 2, WHITE, 0.3)])
    minis = "".join(placed(f'<use href="#h-flake" stroke="{c}" transform="rotate({r} 512 512)" opacity="0.7"/>',
                           x * w, y * h, z * h)
                    for x, y, z, r, c in [(0.12, 0.16, 0.11, 20, YELLOW), (0.86, 0.20, 0.08, -12, CYAN),
                                          (0.16, 0.82, 0.09, 33, RED), (0.83, 0.78, 0.07, 5, WHITE),
                                          (0.70, 0.09, 0.05, 40, RED), (0.30, 0.55, 0.04, 12, CYAN)])
    pixels = wall_pixels(rnd, w, h, 260, (cx, cy, 0.42 * h, 0.42 * h))
    return (f'<defs>{hero_defs("h-")}{clips}</defs><rect width="{w}" height="{h}" fill="{BG}"/>'
            f'{lines}{pixels}{minis}{hero}{slices}')


def wall_snowfall(w, h):
    """Flakes of every size: small and dim far away, big and RGB-split up close."""
    rnd = random.Random(41)
    size_of = lambda z: (0.025 + 0.20 * z ** 2) * h
    flakes, big = [], []
    while len(flakes) < int(80 * w / h):
        z = rnd.random() ** 1.8                     # most of them far away
        x, y = rnd.uniform(-0.03, 1.03) * w, rnd.uniform(-0.05, 1.05) * h
        if z > 0.5:                                 # the near ones do not overlap each other
            if any((x - bx) ** 2 + (y - by) ** 2 < (0.55 * (size_of(z) + bs)) ** 2 for bx, by, bs in big):
                continue
            big.append((x, y, size_of(z)))
        flakes.append((z, x, y, rnd.uniform(0, 60)))
    out = []
    for z, x, y, r in sorted(flakes):
        size = size_of(z)
        if z > 0.78:                                # close: the hero's split
            body = (f'<g transform="rotate({r} 512 512)"><use href="#h-flake" stroke="{RED}" transform="translate(-16 6)" '
                    f'opacity="0.85"/><use href="#h-flake" stroke="{CYAN}" transform="translate(16 -6)" opacity="0.85"/>'
                    f'<use href="#h-flake" stroke="{WHITE}"/></g>')
        else:
            c = rnd.choices([WHITE, CYAN, RED, YELLOW], [6, 2, 2, 1])[0]
            body = (f'<use href="#h-flake" stroke="{c}" transform="rotate({r} 512 512)" '
                    f'opacity="{0.18 + 0.6 * z:.2f}"/>')
        out.append(placed(body, x, y, size))
    pixels = wall_pixels(rnd, w, h, 90, opacity=(0.15, 0.3, 0.45))
    return f'<defs>{hero_defs("h-")}</defs><rect width="{w}" height="{h}" fill="{BG}"/>{pixels}{"".join(out)}'


def wall_split(w, h):
    """The hero's three colours as huge outlines, pulled apart and cut by the bands across the whole screen."""
    cx, cy, size = 0.60 * w, 0.52 * h, 1.55 * h
    dx, dy = 0.022 * h, 0.008 * h
    arm = (f'<g id="w-arm" fill="none" stroke-width="16" stroke-linecap="round" stroke-linejoin="round">{ARM}</g>'
           f'<g id="w-flake" transform="rotate({TILT} 512 512)">{six("w-arm")}</g>')
    bands = (f'<mask id="w-bands" maskUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}">'
             f'<rect width="{w}" height="{h}" fill="#fff"/>'
             + "".join(f'<rect x="0" y="{y * h:.0f}" width="{w}" height="{t * h:.0f}" fill="#000"/>'
                       for y, t in [(0.29, 0.012), (0.47, 0.028), (0.66, 0.009), (0.81, 0.02)]) + '</mask>')
    layers = "".join(
        placed(f'<use href="#w-flake" stroke="{c}" opacity="{o}" style="mix-blend-mode:screen"/>', cx + ox, cy + oy, size)
        for c, ox, oy, o in [(RED, -dx, dy, 0.9), (CYAN, dx, -dy, 0.9), (WHITE, 0, 0, 1)])
    return (f'<defs>{arm}{bands}</defs><rect width="{w}" height="{h}" fill="{BG}"/>'
            f'<g mask="url(#w-bands)" style="isolation:isolate">{layers}</g>')


def wall_quiet(w, h):
    """Nearly empty: a faint ghost of the hero to the right, for working without distraction."""
    cx, cy, size = 0.70 * w, 0.56 * h, 1.25 * h
    t = f"rotate({TILT} 512 512)"
    ghost = (f'<g mask="url(#h-bands)">'
             f'<use href="#h-flake" stroke="{RED}" transform="translate(-16 6) {t}" opacity="0.07"/>'
             f'<use href="#h-flake" stroke="{CYAN}" transform="translate(16 -6) {t}" opacity="0.07"/>'
             f'<use href="#h-flake" stroke="{WHITE}" transform="{t}" opacity="0.06"/></g>')
    return f'<defs>{hero_defs("h-")}</defs><rect width="{w}" height="{h}" fill="{BG}"/>{placed(ghost, cx, cy, size)}'


def wall_mono(w, h):
    """Subdued, greyscale on pure black: the hero alone, centred, its split in greys, no pixels or small flakes."""
    t = f"rotate({TILT} 512 512)"
    flake = (f'<g mask="url(#h-bands)">'
             f'<use href="#h-flake" stroke="#2E2E2E" transform="translate(-16 6) {t}"/>'
             f'<use href="#h-flake" stroke="#4A4A4A" transform="translate(16 -6) {t}"/>'
             f'<use href="#h-flake" stroke="#8C8C8C" transform="{t}"/></g>')
    return (f'<defs>{hero_defs("h-")}</defs><rect width="{w}" height="{h}" fill="#000000"/>'
            + placed(flake, w / 2, h / 2, 0.42 * h))


WALLPAPERS = {"glitch": wall_glitch, "snowfall": wall_snowfall, "split": wall_split, "quiet": wall_quiet, "mono": wall_mono}


def wallpapers():
    """Writes svg/wallpapers/ (the masters) and wallpapers/ (the PNGs the guests use)."""
    for name, draw in WALLPAPERS.items():
        for w, h in WALL_SIZES:
            src = os.path.join(SVG, "wallpapers", f"omaflake-{name}-{w}x{h}.svg")
            write(src, svg(f"0 0 {w} {h}", draw(w, h), w))
            render(src, os.path.join(HERE, "wallpapers", f"omaflake-{name}-{w}x{h}.png"), w, h)


# --- export ----------------------------------------------------------------------------------

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def render(src, dst, w, h=None):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h or w), src, "-o", dst], check=True)


def ico(dst, pngs):
    """favicon.ico with embedded PNGs."""
    data = [open(p, "rb").read() for _, p in pngs]
    out = struct.pack("<HHH", 0, 1, len(pngs))
    offset = 6 + 16 * len(pngs)
    for (size, _), d in zip(pngs, data):
        out += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(d), offset)
        offset += len(d)
    with open(dst, "wb") as f:
        f.write(out + b"".join(data))


def main():
    masters = {
        "omaflake-icon.svg": app_icon(),
        "omaflake-icon-small.svg": app_icon_small(),
        "omaflake-icon-square.svg": fullbleed(),
        "omaflake-mark-on-dark.svg": mark(WHITE),
        "omaflake-mark-on-light.svg": mark(BG),
        "omaflake-glyph-black.svg": glyph("#000000"),
        "omaflake-glyph-white.svg": glyph(WHITE),
        "omaflake-glyph-small-black.svg": glyph_small("#000000"),
        "omaflake-glyph-small-white.svg": glyph_small(WHITE),
        "omaflake-menubarTemplate.svg": menubar(),
        "favicon.svg": favicon(),
        "omaflake-social.svg": social(),
    }
    for name, content in masters.items():
        write(os.path.join(SVG, name), content)
    s = lambda n: os.path.join(SVG, n)

    for n in (16, 32, 64, 128, 256, 512, 1024):
        render(s("omaflake-icon-small.svg" if n <= 32 else "omaflake-icon.svg"), f"{PNG}/icon/omaflake-icon-{n}.png", n)
    for n in (128, 256, 512, 1024):
        render(s("omaflake-icon-square.svg"), f"{PNG}/icon-square/omaflake-icon-square-{n}.png", n)
    for v in ("on-dark", "on-light"):
        for n in (64, 128, 256, 512, 1024):
            render(s(f"omaflake-mark-{v}.svg"), f"{PNG}/mark/omaflake-mark-{v}-{n}.png", n)
    for v in ("black", "white"):
        for n in (32, 64, 128, 256, 512, 1024):
            render(s(f"omaflake-glyph-{v}.svg"), f"{PNG}/glyph/omaflake-glyph-{v}-{n}.png", n)
        for n in (16, 18, 24, 32, 48):
            render(s(f"omaflake-glyph-small-{v}.svg"), f"{PNG}/glyph-small/omaflake-glyph-small-{v}-{n}.png", n)
    # The NixOS guests' loading screen: the Plymouth theme's images (plymouth/, omaflake's nix/modules/plymouth/) and
    # the image QEMU shows until the guest draws it (png/loading/, embedded in omaf)
    loading_screen(os.path.join(HERE, "plymouth"), f"{PNG}/loading/omaflake-loading.png")
    wallpapers()
    for scale, suffix in ((1, ""), (2, "@2x"), (3, "@3x")):
        render(s("omaflake-menubarTemplate.svg"), f"{PNG}/menubar/omaflakeTemplate{suffix}.png", 18 * scale)

    web = os.path.join(HERE, "web")
    for n in (16, 32, 48):
        render(s("favicon.svg"), f"{web}/favicon-{n}.png", n)
    ico(f"{web}/favicon.ico", [(n, f"{web}/favicon-{n}.png") for n in (16, 32, 48)])
    shutil.copy(s("favicon.svg"), f"{web}/favicon.svg")
    render(s("omaflake-icon-square.svg"), f"{web}/apple-touch-icon.png", 180)
    for n in (192, 512):
        render(s("omaflake-icon-square.svg"), f"{web}/icon-{n}.png", n)
    write(f"{web}/site.webmanifest",
          '{\n  "name": "omaflake",\n  "short_name": "omaflake",\n  "icons": [\n'
          '    { "src": "icon-192.png", "sizes": "192x192", "type": "image/png" },\n'
          '    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png" }\n  ],\n'
          f'  "theme_color": "{BG}",\n  "background_color": "{BG}",\n  "display": "standalone"\n}}\n')

    social_dir = os.path.join(PNG, "social")
    render(s("omaflake-social.svg"), f"{social_dir}/omaflake-social-1280x640.png", 1280, 640)
    render(s("omaflake-icon-square.svg"), f"{social_dir}/github-avatar-500.png", 500)

    # macOS app icon
    iconset = os.path.join(HERE, "macos", "omaflake.iconset")
    os.makedirs(iconset, exist_ok=True)
    for base in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            px = base * scale
            src = "omaflake-icon-small.svg" if px <= 32 else "omaflake-icon.svg"
            render(s(src), f"{iconset}/icon_{base}x{base}{'@2x' if scale == 2 else ''}.png", px)
    subprocess.run(["iconutil", "-c", "icns", iconset, "-o", os.path.join(HERE, "macos", "omaflake.icns")], check=True)
    print("ok – now python3 copy.py")


if __name__ == "__main__":
    main()
