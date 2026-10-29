#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Copies the artwork the other omaflake repositories use into their checkouts next to this one (../omaflake,
../website, ../catalog). They keep the copies as they are – change the artwork here, run generate.py, then this.
A checkout that is not there is skipped. Afterwards, in omaflake: `python3 brand/tokens.py` (it embeds the copied
icons in BrandAssets.swift).

    python3 copy.py [--root <folder with the checkouts>]
"""
import glob, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# (repository, source in this repository – a glob –, target folder in that repository)
COPIES = [
    ("omaflake", "macos/omaflake.icns", "brand/macos"),
    ("omaflake", "png/icon/*.png", "brand/png/icon"),
    ("omaflake", "svg/omaflake-icon.svg", "brand/svg"),
    ("omaflake", "png/glyph-small/omaflake-glyph-small-white-48.png", "brand/png/glyph-small"),
    ("omaflake", "png/menubar/*.png", "brand/png/menubar"),
    ("omaflake", "png/loading/omaflake-loading.png", "brand/png/loading"),
    ("omaflake", "png/social/omaflake-social-1280x640.png", "brand/png/social"),
    ("omaflake", "plymouth/*", "nix/modules/plymouth"),
    ("omaflake", "web/favicon.ico", "docs/assets"),
    ("omaflake", "web/favicon.svg", "docs/assets"),
    ("omaflake", "svg/omaflake-mark-on-dark.svg", "docs/assets"),
    ("website", "web/*", "."),
    ("website", "png/mark/omaflake-mark-on-dark-512.png", "assets"),
    ("website", "png/social/omaflake-social-1280x640.png", "assets/og.png"),
    ("catalog", "macos/omaflake.icns", "modules/omaflake/macos/omaflake-dev/omaflake-test.icns"),
]


def main():
    args = sys.argv[1:]
    root = os.path.abspath(args[args.index("--root") + 1]) if "--root" in args else os.path.dirname(HERE)
    for repo, pattern, target in COPIES:
        checkout = os.path.join(root, repo)
        if not os.path.isdir(checkout):
            print("skipped", repo, "(no checkout)")
            continue
        sources = sorted(glob.glob(os.path.join(HERE, pattern)))
        if not sources:
            raise SystemExit(f"nothing matches {pattern} – run generate.py first")
        for src in sources:
            dst = os.path.join(checkout, target)
            if os.path.splitext(target)[1] == "":
                dst = os.path.join(dst, os.path.basename(src))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            print("copied", os.path.relpath(src, HERE), "→", os.path.relpath(dst, root))


if __name__ == "__main__":
    main()
