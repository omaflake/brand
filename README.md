# omaflake – brand kit

The one source of omaflake's look: the marks, the palette, the generator and every export. The other repositories
carry copies of what they show, written by `copy.py`, and never edit them there.

Two marks:

- **Hero** (chaotic, RGB-split snowflake on near-black) – app icon, GitHub, website, social.
- **Glyph** (the hero flake in one colour: same tilt, no RGB split, no glitch bands, no background) –
  monochrome use. **Small glyph** (same tilt, one chevron per arm, heavy stroke) – menu bar, favicon, 16–48 px.

Everything is generated: edit `generate.py` (the drawing) and `palette.toml` (the colours), not the exported files.

```sh
python3 generate.py   # svg/, png/, web/, macos/, plymouth/ – needs Python 3.11+, rsvg-convert (Homebrew: librsvg), iconutil (macOS)
python3 copy.py       # copies into ../omaflake, ../website, ../catalog (checkouts next to this one)
```

Then, in `omaflake`: `python3 brand/tokens.py` (it embeds the copied icons in `BrandAssets.swift`). A colour change
also goes into omaflake's design tokens, `brand/tokens.toml` `[palette]`, which is a copy of `palette.toml`.

## Where to use what

| Use | File |
|---|---|
| macOS app icon | `macos/omaflake.icns` (16/32 px slots: small glyph on the icon background) |
| Menu bar (template image, macOS tints it) | `png/menubar/omaflakeTemplate.png`, `@2x`, `@3x` or `svg/omaflake-menubarTemplate.svg` |
| GitHub organisation avatar | `png/social/github-avatar-500.png` |
| GitHub social preview (repository settings), link previews | `png/social/omaflake-social-1280x640.png` |
| Website `<head>` | `web/` – favicon.ico, favicon.svg (transparent, adapts to light/dark), apple-touch-icon.png, icon-192/512.png, site.webmanifest |
| README / docs header | `png/mark/omaflake-mark-on-dark-*.png` or `-on-light-*.png` (transparent), `svg/omaflake-mark-on-*.svg` |
| Rounded app icon as image | `png/icon/omaflake-icon-*.png` (transparent corners, macOS grid) |
| Square, edge-to-edge | `png/icon-square/omaflake-icon-square-*.png` |
| Monochrome (stickers, print, single colour) | `svg/omaflake-glyph-black.svg`, `-white.svg`, `png/glyph/` |
| Monochrome, tiny (16–48 px) | `svg/omaflake-glyph-small-black.svg`, `-white.svg`, `png/glyph-small/` |
| NixOS guests' loading screen | `plymouth/` (the Plymouth theme's images and `layout.script`) and `png/loading/omaflake-loading.png` (its first frame, which QEMU's window shows until the guest draws); sources in `svg/loading/` |

Website head:

```html
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
```

## Where it is used

`copy.py` holds the list; in short:

| Repository | Copies |
|---|---|
| `omaflake/omaflake` | `brand/` (icns, icons, menu bar, small glyph, loading frame, social preview), `nix/modules/plymouth/`, `docs/assets/` (favicons, mark on dark) |
| `omaflake/website` | `web/` (root), `assets/` (mark on dark 512, `og.png` = the social preview) |
| `omaflake/catalog` | `modules/omaflake/macos/omaflake-dev/omaflake-test.icns` (the icns) |
| `omaflake/.github` | the profile banner `profile/assets/omaflake-banner.png` – not generated here (OPEN: move its source here) |

## Colours

| Name | Hex |
|---|---|
| Background | `#121212` |
| Red | `#FF3B3B` |
| Cyan | `#00E5FF` |
| Yellow | `#F5FF3B` |
| White | `#FFFFFF` |

Source: `palette.toml`.

Wordmark: `omaflake` in lowercase, Menlo Bold (monospace), with the same red/cyan offset as the hero.

## Direction: icons for the things in the app (2026-10-18, later)

The app uses SF Symbols today (monitor = VM, package = image, book = recipe; actions as a small cyan sub-symbol).
Own icons may take up the snow of the logo: VM = snowman, image = snowball, recipe = snow; the flake stays the Nix
flake behind it all (not shown in the app). Same rules as the glyph: one weight, readable at 13 pt, red/cyan only as
accents.

## Licences and rights

| Files | Licence |
|---|---|
| `generate.py`, `copy.py`, `palette.toml`, this README | [MIT](LICENSES/MIT.txt) |
| the artwork: `svg/`, `png/`, `web/`, `macos/`, `plymouth/` | [CC BY-ND 4.0](LICENSES/CC-BY-ND-4.0.txt) |

The artwork may be copied and passed on – also in apps distributed through app stores and in other software – as it
is and naming falkOSS; changed versions may not be passed on. The licence covers the artwork's copyright, not the
name: omaflake's name and brand belong to falkOSS – Falcon Lake Open Source Software gUG (haftungsbeschränkt) i. G.,
the publisher of omaflake. They may be used to refer to omaflake, not for other products or in a way that suggests
endorsement. The look stays omaflake's own – falkOSS's design is not used here; project pages say "a falkOSS project"
at most. **OPEN**: trademark search and registration, and a review of these terms by someone who knows the law.
