"""Self-generated contribution snake (pure SVG + SMIL, no third-party action, no extra branch).

Reads the same contribution calendar the other cards use, walks a snake over the whole graph column by column and
makes every cell that holds contributions disappear as the snake eats it. Rebuilt on every profile refresh, so it
always reflects your latest contributions. Dark + light builds.
"""
import datetime as dt
from common import USER, SANS, esc
from intro import PAL

CELL, PITCH, LEN = 12, 15, 6          # cell size, grid pitch, snake length (segments)
DT = 0.07                              # seconds per step
PAUSE = 2.5                            # rest at the end before the loop restarts

LEVELS = {
    "dark":  ["#2b2145", "#5b4596", "#8468d0", "#b79cf2", "#e0cfff"],
    "light": ["#ece6fa", "#cdbdf5", "#a98bf0", "#7c55d9", "#4f2fb0"],
}


def _level(n, mx):
    if n <= 0 or mx <= 0:
        return 0
    r = n / mx
    return 1 if r <= .25 else 2 if r <= .5 else 3 if r <= .75 else 4


def build_snake(days, mode):
    P, cols_c = PAL[mode], LEVELS[mode]
    n = len(days)
    cols = (n + 6) // 7
    gw, gh = cols * PITCH - (PITCH - CELL), 7 * PITCH - (PITCH - CELL)
    W, pad_t, pad_b = 830, 34, 40
    H = pad_t + gh + pad_b
    ox, oy = (W - gw) / 2, pad_t
    mx = max((d["count"] for d in days), default=0)

    def xy(i):                                         # grid cell of the i-th day (Sunday-first weeks, top to bottom)
        return ox + (i // 7) * PITCH, oy + (i % 7) * PITCH

    # snake route: down column 0, up column 1, ... (only cells that exist)
    route = []
    for c in range(cols):
        rows = [r for r in range(7) if c * 7 + r < n]
        route += [c * 7 + r for r in (rows if c % 2 == 0 else reversed(rows))]
    pos = [xy(i) for i in route]
    steps = len(pos)
    ex, ey = pos[-1]
    pos += [(ex + (j + 1) * PITCH, ey) for j in range(LEN + 2)]       # glide off the right edge
    m = len(pos)
    total = m * DT + PAUSE
    kt = [f"{i * DT / total:.5f}" for i in range(m)] + ["1"]
    arrive = {cell: s for s, cell in enumerate(route)}

    cells = []
    for i, d in enumerate(days):
        x, y = xy(i)
        lv = _level(d["count"], mx)
        base = f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="3" fill="{cols_c[lv]}"'
        if lv:
            t = arrive[i] * DT / total
            cells.append(base + f'><animate attributeName="opacity" calcMode="discrete" values="1;0;0" keyTimes="0;{t:.5f};1" '
                                f'dur="{total:.2f}s" repeatCount="indefinite"/></rect>')
        else:
            cells.append(base + "/>")

    segs = []
    for k in range(LEN):
        vals = [pos[max(0, s - k)] for s in range(m)]
        v = ";".join(f"{x:.1f} {y:.1f}" for x, y in vals) + f";{vals[-1][0]:.1f} {vals[-1][1]:.1f}"
        color = P["pink"] if k == 0 else P["lav"]
        op = 1 - k * 0.11
        r = 4 if k == 0 else 3.4
        eye = (f'<circle cx="{CELL-4}" cy="4" r="1.3" fill="{P["bg0"]}"/>' if k == 0 else "")
        segs.append(f'<g opacity="{op:.2f}"><animateTransform attributeName="transform" type="translate" calcMode="discrete" '
                    f'values="{v}" keyTimes="{";".join(kt)}" dur="{total:.2f}s" repeatCount="indefinite"/>'
                    f'<rect width="{CELL}" height="{CELL}" rx="{r}" fill="{color}"/>{eye}</g>')
    segs.reverse()                                     # head drawn last = on top

    eaten = sum(1 for d in days if d["count"] > 0)
    total_c = sum(d["count"] for d in days)
    label = f"Contribution snake: {total_c} contribution{'' if total_c == 1 else 's'} over the last year"
    stamp = f"@{USER} · {total_c:,} contribution{'' if total_c == 1 else 's'} in the last year"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(label)}">'
           f'<title>{esc(label)}</title>'
           f'<defs><linearGradient id="sbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{P["bg0"]}"/><stop offset="1" stop-color="{P["bg1"]}"/></linearGradient></defs>'
           f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="22" fill="url(#sbg)" stroke="{P["line"]}" stroke-opacity="{P["line_op"]}"/>'
           f'{"".join(cells)}{"".join(segs)}'
           f'<text x="{W-24}" y="{H-14}" text-anchor="end" font-family="{SANS}" font-size="11" fill="{P["faint"]}">{esc(stamp)}</text></svg>')
    return svg
