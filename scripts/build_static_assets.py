#!/usr/bin/env python3
"""Builds the STATIC art (banner, lanyard, toolkit, fields, headings, buttons, footer).

Run this only when you change the design or the portrait:   python scripts/build_static_assets.py
The live data cards are built separately by scripts/generate_profile.py.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _prep_images import banner_image_b64, badge_image_b64
from banner import build_banner, DARK, LIGHT
from intro import build_intro_scene, build_interests
from lanyard import build_lanyard
import static_parts as sp

ASSETS = Path(__file__).resolve().parent.parent / "assets"
HEADINGS = ["Introduction", "Primary Fields", "Interests", "Toolkit", "Featured Projects", "GitHub Statistics",
            "Contribution Graph", "Languages", "GitHub Snake", "Connect With Me"]
FIELDS = ["Data Analytics", "Python Development", "Agentic AI", "Artificial Intelligence & Machine Learning",
          "Healthcare Technology", "AI-powered Solutions", "Computer Vision", "Creative Technology"]
QUOTE = ["Build with intelligence, create with purpose,", "and let technology become an extension of your creativity."]


def slug(s):
    return s.lower().replace(" ", "-")


def main():
    ASSETS.mkdir(exist_ok=True, parents=True)
    (ASSETS / "headings").mkdir(exist_ok=True)
    b = banner_image_b64()
    out = {
        "banner.svg": build_banner(DARK, b),
        "banner-light.svg": build_banner(LIGHT, b),
        "intro-dark.svg": build_intro_scene(None, "dark", badge=False),
        "intro-light.svg": build_intro_scene(None, "light", badge=False),
        "lanyard-dark.svg": build_lanyard(badge_image_b64(), "dark")[0],
        "lanyard-light.svg": build_lanyard(badge_image_b64(), "light")[0],
        "interests-dark.svg": build_interests("dark"),
        "interests-light.svg": build_interests("light"),
        "toolkit.svg": sp.toolkit(),
        "fields.svg": sp.fields(FIELDS),
        "connect-email.svg": sp.button("email"),
        "connect-github.svg": sp.button("github"),
        "footer.svg": sp.footer(QUOTE),
    }
    for h in HEADINGS:
        out[f"headings/{slug(h)}.svg"] = sp.heading(h)
    for name, svg in out.items():
        (ASSETS / name).write_text(svg, encoding="utf-8")
        print(f"wrote assets/{name}  ({len(svg)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
