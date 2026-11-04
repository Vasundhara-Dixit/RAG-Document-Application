"""Shared constants + styling helpers for the profile generators."""
from html import escape as _esc

USER = "Vasundhara-Dixit"
NAME = "Vasundhara Dixit"
EMAIL = "vasudixit1826@gmail.com"
GITHUB_URL = f"https://github.com/{USER}"

SERIF = "'Playfair Display','Cormorant Garamond',Georgia,'Times New Roman',serif"
SANS = "'Inter','Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','SF Mono',SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"

# Adaptive palette for the small cards / headings (light by default, dark via media query).
CARD_CSS = f"""
:root{{--bg0:#fbf8ff;--bg1:#fff1f8;--ink:#2a1f45;--muted:#5d4f80;--faint:#8a7ca8;--line:#8f74d8;
--lav:#6c4dc4;--pink:#d2467f;--emerald:#178a63;--gold:#9a741d;--sky:#3f73c4;--tile:#ffffff;--tileop:.66;--track:#e6def7}}
@media (prefers-color-scheme:dark){{:root{{--bg0:#160f24;--bg1:#221636;--ink:#f6f0ff;--muted:#bcaedb;--faint:#8f80b3;
--line:#cbb8ff;--lav:#cbb8ff;--pink:#ffb8d6;--emerald:#6fe0b0;--gold:#e9cf8f;--sky:#9dbcf2;--tile:#ffffff;--tileop:.06;--track:#33254d}}}}
.serif{{font-family:{SERIF}}} .sans{{font-family:{SANS}}} .mono{{font-family:{MONO}}}
.ink{{fill:var(--ink)}} .muted{{fill:var(--muted)}} .faint{{fill:var(--faint)}}
.lav{{fill:var(--lav)}} .pink{{fill:var(--pink)}} .emerald{{fill:var(--emerald)}} .gold{{fill:var(--gold)}}
.g0{{stop-color:var(--bg0)}} .g1{{stop-color:var(--bg1)}}
.sl{{stop-color:var(--lav)}} .sp{{stop-color:var(--pink)}} .se{{stop-color:var(--emerald)}} .sg{{stop-color:var(--gold)}}
.card{{stroke:var(--line);stroke-opacity:.32;stroke-width:1}}
.tile{{fill:var(--tile);fill-opacity:var(--tileop);stroke:var(--line);stroke-opacity:.26;stroke-width:1}}
.track{{fill:var(--track)}}
"""


def esc(s) -> str:
    return _esc(str(s), quote=True)


def fmt_num(n: int) -> str:
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".replace(".0M", "M")
    if n >= 10_000:
        return f"{n/1000:.1f}k".replace(".0k", "k")
    return f"{n:,}"
