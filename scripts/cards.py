"""Self-generated stat cards (pure SVG + SMIL). Adaptive light/dark through CSS variables."""
import datetime as dt
import math
from common import CARD_CSS, USER, esc, fmt_num
from static_parts import _chip, est, DOT_CLASSES

W = 830
LANG_COLORS = ["#b79cf2", "#f4a3c6", "#62cfa3", "#e8c877", "#8fb8f0", "#f5b08a", "#a99fc4", "#7fd0d6", "#d9a6e8"]


def _frame(w, h, label, body, defs="", stamp=""):
    st = (f'<text x="{w-24}" y="{h-14}" text-anchor="end" class="sans faint" font-size="11">{esc(stamp)}</text>' if stamp else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}">'
            f'<title>{esc(label)}</title><style>{CARD_CSS}.sky{{fill:var(--sky)}}.ss{{stop-color:var(--sky)}}</style>'
            f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop class="g0" offset="0"/><stop class="g1" offset="1"/></linearGradient>'
            f'<radialGradient id="ga"><stop class="sl" offset="0" stop-opacity=".22"/><stop class="sl" offset="1" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="gb"><stop class="sp" offset="0" stop-opacity=".20"/><stop class="sp" offset="1" stop-opacity="0"/></radialGradient>{defs}</defs>'
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="22" fill="url(#bg)" class="card"/>'
            f'<circle cx="60" cy="0" r="220" fill="url(#ga)"/><circle cx="{w-40}" cy="{h}" r="240" fill="url(#gb)"/>{body}{st}</svg>')


def _stamp(data):
    d = dt.datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
    return f"@{USER} · updated {d.strftime('%b %d, %Y')} UTC"


# ------------------------------------------------------------------ stats
def stats_card(d):
    years = d.get("years")
    tiles = [
        ("Public repositories", fmt_num(d["public_repos"]), "sl"),
        ("Stars earned", fmt_num(d["stars_earned"]), "sg"),
        ("Followers", fmt_num(d["followers"]), "sp"),
        ("Following", fmt_num(d["following"]), "se"),
        ("Contributions, last year", fmt_num(d["contrib_total"]), "sl"),
        ("Pull requests", fmt_num(d["prs"]), "sp"),
        ("Issues opened", fmt_num(d["issues"]), "se"),
        ("Joined GitHub", str(d["joined_year"]) if d.get("joined_year") else "—", "sg"),
    ]
    tw, th, gap, pad = 181, 80, 14, 32
    body = []
    for i, (label, val, cls) in enumerate(tiles):
        x = pad + (i % 4) * (tw + gap); y = 26 + (i // 4) * (th + gap)
        begin = f"{0.15 + i * 0.07:.2f}s"
        body.append(
            f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur=".7s" begin="{begin}" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 8;0 0" calcMode="spline" keyTimes="0;1" keySplines=".2 .7 .2 1" dur=".7s" begin="{begin}" fill="freeze"/>'
            f'<rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="16" class="tile"/>'
            f'<rect x="{x+14}" y="{y+18}" width="3" height="44" rx="1.5" style="fill:var(--{ {"sl":"lav","sp":"pink","se":"emerald","sg":"gold"}[cls] })"/>'
            f'<text x="{x+30}" y="{y+44}" class="serif ink" font-size="32" font-weight="700">{esc(val)}</text>'
            f'<text x="{x+30}" y="{y+64}" class="sans muted" font-size="12">{esc(label)}</text></g>')
    h = 26 + 2 * th + gap + 46
    return _frame(W, h, f"GitHub statistics for {USER}", "".join(body), stamp=_stamp(d))


# ------------------------------------------------------------------ languages
PINNED_SKILLS = ["Python", "C++", "PyTorch", "TensorFlow", "Pytest", "HTML5", "CSS"]   # always shown, edit here


def _skill_chips(items, top=26, size=15, h=34, gap=12, maxw=W - 64):
    rows, cur, curw = [], [], 0
    for it in items:
        w = est(it, size) + 40
        if cur and curw + gap + w > maxw:
            rows.append((cur, curw)); cur, curw = [], 0
        curw += (gap if cur else 0) + w; cur.append((it, w))
    if cur:
        rows.append((cur, curw))
    out, k = [], 0
    for ri, (row, rw) in enumerate(rows):
        x, y = (W - rw) / 2, top + ri * (h + gap)
        for it, w in row:
            out.append(_chip(x, y, it, DOT_CLASSES[k % 5], size=size, h=h)[1]); k += 1; x += w + gap
    return "".join(out), top + len(rows) * (h + gap) - gap


def langs_card(d):
    chips, chips_h = _skill_chips(PINNED_SKILLS)
    live = _langs_live(d)
    if live is None:                                   # no GitHub language data yet: just the pinned skills
        return _frame(W, chips_h + 52, "Languages and frameworks: " + ", ".join(PINNED_SKILLS), chips, "", _stamp(d))
    body, defs, h, label = live
    dy = chips_h + 22
    sep = f'<rect x="32" y="{chips_h+11}" width="{W-64}" height="1" class="card" style="fill:var(--line);fill-opacity:.25"/>'
    return _frame(W, h + dy, "Languages and frameworks: " + ", ".join(PINNED_SKILLS) + ". " + label,
                  chips + sep + f'<g transform="translate(0 {dy})">{body}</g>', defs, _stamp(d))


def _langs_live(d):
    langs = sorted(d["languages"].items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in langs)
    x0, bw, by, bh = 32, W - 64, 30, 16
    body = []
    defs = f'<clipPath id="pill"><rect x="{x0}" y="{by}" width="{bw}" height="{bh}" rx="{bh/2}"/></clipPath>'
    if total <= 0:
        return None
    top = langs[:8]
    other = sum(v for _, v in langs[8:])
    items = top + ([("Other", other)] if other else [])
    x = x0
    segs = []
    for i, (n, v) in enumerate(items):
        w = bw * v / total
        segs.append(f'<rect x="{x:.2f}" y="{by}" width="{max(w-2,1):.2f}" height="{bh}" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>')
        x += w
    defs += (f'<clipPath id="reveal"><rect x="{x0}" y="{by-4}" width="0" height="{bh+8}"><animate attributeName="width" values="0;{bw}" '
             f'calcMode="spline" keyTimes="0;1" keySplines=".4 0 .2 1" dur="1.4s" begin=".2s" fill="freeze"/></rect></clipPath>')
    body.append(f'<rect x="{x0}" y="{by}" width="{bw}" height="{bh}" rx="{bh/2}" class="track"/>')
    body.append(f'<g clip-path="url(#pill)"><g clip-path="url(#reveal)">{"".join(segs)}</g></g>')
    cols, colw, ly = 3, (W - 64) / 3, by + 52
    for i, (n, v) in enumerate(items):
        cx = x0 + (i % cols) * colw; cy = ly + (i // cols) * 30
        pct = 100 * v / total
        body.append(
            f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur=".6s" begin="{0.5 + i*0.06:.2f}s" fill="freeze"/>'
            f'<circle cx="{cx+6}" cy="{cy-4}" r="5.5" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>'
            f'<text x="{cx+20}" y="{cy}" class="sans ink" font-size="14" font-weight="500">{esc(n)}</text>'
            f'<text x="{cx+colw-28}" y="{cy}" text-anchor="end" class="mono muted" font-size="13">{pct:.1f}%</text></g>')
    rows = math.ceil(len(items) / cols)
    h = ly + rows * 30 + 26
    return "".join(body), defs, h, "Top languages on GitHub: " + ", ".join(f"{n} {100*v/total:.0f}%" for n, v in items)


# ------------------------------------------------------------------ contribution graph
def _weeks(days):
    out = []
    for i in range(0, len(days), 7):
        chunk = days[i:i + 7]
        out.append((chunk[0]["date"], sum(c["count"] for c in chunk)))
    return out


def _streaks(days):
    longest = cur = 0
    for c in days:
        cur = cur + 1 if c["count"] > 0 else 0
        longest = max(longest, cur)
    cs = 0
    i = len(days) - 1
    if i >= 0 and days[i]["count"] == 0:
        i -= 1
    while i >= 0 and days[i]["count"] > 0:
        cs += 1; i -= 1
    return cs, longest


def _nice(m):
    for c in [4, 8, 12, 20, 40, 60, 100, 150, 200, 300, 500, 800, 1200, 2000, 5000]:
        if m <= c:
            return c
    return int(math.ceil(m / 1000) * 1000)


def _smooth(pts, top, base):
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, min(base, max(top, p1[1] + (p2[1] - p0[1]) / 6)))
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, min(base, max(top, p2[1] - (p3[1] - p1[1]) / 6)))
        d += f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def activity_card(d):
    days = d["contrib_days"]
    weeks = _weeks(days)
    total = sum(c["count"] for c in days)
    best = max(days, key=lambda c: c["count"]) if days else {"count": 0, "date": ""}
    cur, longest = _streaks(days)
    tiles = [("Contributions, last year", fmt_num(total)),
             ("Best day", f'{best["count"]}' + (f' · {dt.date.fromisoformat(best["date"]).strftime("%b %d")}' if best["count"] else "")),
             ("Current streak", f"{cur} day{'s' if cur != 1 else ''}"), ("Longest streak", f"{longest} day{'s' if longest != 1 else ''}")]
    tw, th, gap = 181, 62, 14
    body = []
    for i, (label, val) in enumerate(tiles):
        x = 32 + i * (tw + gap)
        body.append(f'<rect x="{x}" y="24" width="{tw}" height="{th}" rx="14" class="tile"/>'
                    f'<text x="{x+18}" y="{24+34}" class="serif ink" font-size="24" font-weight="700">{esc(val)}</text>'
                    f'<text x="{x+18}" y="{24+53}" class="sans muted" font-size="11.5">{esc(label)}</text>')
    x0, x1, top, base = 62, 800, 128, 252
    vals = [w[1] for w in weeks] or [0]
    ymax = _nice(max(vals))
    n = max(len(weeks), 2)
    pts = [(x0 + (x1 - x0) * i / (n - 1), base - (base - top) * (v / ymax)) for i, (_, v) in enumerate(weeks)]
    if len(pts) < 2:
        pts = [(x0, base), (x1, base)]
    for frac in (0, .5, 1):
        y = base - (base - top) * frac
        body.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" style="stroke:var(--line)" stroke-opacity="{.28 if frac else .5}" stroke-dasharray="{"3 5" if frac else "0"}"/>')
        body.append(f'<text x="{x0-10}" y="{y+4:.1f}" text-anchor="end" class="mono faint" font-size="10.5">{int(ymax*frac)}</text>')
    line = _smooth(pts, top, base)
    area = f'{line}L{pts[-1][0]:.1f},{base}L{pts[0][0]:.1f},{base}Z'
    defs = ('<linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop class="sl" offset="0" stop-opacity=".45"/><stop class="sp" offset="1" stop-opacity="0"/></linearGradient>'
            '<linearGradient id="stroke" x1="0" y1="0" x2="1" y2="0"><stop class="sl" offset="0"/><stop class="sp" offset=".65"/><stop class="sg" offset="1"/></linearGradient>')
    body.append(f'<path d="{area}" fill="url(#area)" opacity="0"><animate attributeName="opacity" values="0;1" dur="1.2s" begin="1s" fill="freeze"/></path>')
    body.append(f'<path d="{line}" fill="none" stroke="url(#stroke)" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1">'
                f'<animate attributeName="stroke-dashoffset" values="1;0" calcMode="spline" keyTimes="0;1" keySplines=".4 0 .2 1" dur="2s" begin=".2s" fill="freeze"/></path>')
    if max(vals) > 0:
        pi = vals.index(max(vals)); px, py = pts[pi]
        body.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" class="pink"/><circle cx="{px:.1f}" cy="{py:.1f}" r="9" fill="none" style="stroke:var(--pink)" stroke-opacity=".4"/>'
                    f'<text x="{px + (16 if px < x0 + 24 else 0):.1f}" y="{max(py-14, top-2) + (12 if px < x0 + 24 else 0):.1f}" text-anchor="{"start" if px < x0 + 24 else "middle"}" class="mono ink" font-size="11">{max(vals)}</text>')
    last_m = None
    for i, (date, _) in enumerate(weeks):
        m = date[:7]
        if m != last_m:
            last_m = m
            if pts[i][0] < x1 - 20:
                body.append(f'<text x="{pts[i][0]:.1f}" y="{base+22}" class="sans faint" font-size="11">{dt.date.fromisoformat(date).strftime("%b")}</text>')
    label = f"Contribution activity for the last year: {total} contributions"
    return _frame(W, 306, label, "".join(body), defs, _stamp(d))
