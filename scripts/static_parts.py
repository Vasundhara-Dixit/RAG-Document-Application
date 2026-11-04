"""Small static pieces: section headings, toolkit, fields, connect buttons, footer."""
import datetime
from common import CARD_CSS, NAME, USER, EMAIL, SERIF, SANS, MONO, esc

DOT_CLASSES = ["lav", "pink", "emerald", "gold", "sky"]


def est(text, size):
    """Approximate advance width of proportional sans/serif text (per-glyph classes)."""
    w = 0.0
    for ch in text:
        if ch in "iljI.,:;!|' ":
            w += .30
        elif ch in "mwMW":
            w += .86
        elif ch.isupper():
            w += .68
        elif ch.isdigit():
            w += .58
        elif ch in "&+/@":
            w += .78
        else:
            w += .55
    return w * size


def _svg(w, h, title, body, defs="", desc=""):
    d = f'<desc>{esc(desc)}</desc>' if desc else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{esc(title)}"><title>{esc(title)}</title>{d}<style>{CARD_CSS}.sky{{fill:var(--sky)}}</style>'
            f'<defs>{defs}</defs>{body}</svg>')


def heading(title):
    w, h = 830, 64
    tw = est(title, 27) * 1.04
    x0, x1 = 415 - tw / 2 - 26, 415 + tw / 2 + 26
    defs = ('<linearGradient id="l" x1="0" y1="0" x2="1" y2="0"><stop offset="0" class="sl" stop-opacity="0"/>'
            '<stop offset=".6" class="sp" stop-opacity=".85"/><stop offset="1" class="sg"/></linearGradient>'
            '<linearGradient id="r" x1="1" y1="0" x2="0" y2="0"><stop offset="0" class="sl" stop-opacity="0"/>'
            '<stop offset=".6" class="sp" stop-opacity=".85"/><stop offset="1" class="sg"/></linearGradient>')
    body = (f'<rect x="60" y="31.25" width="{x0-60:.1f}" height="1.5" fill="url(#l)"/>'
            f'<rect x="{x1:.1f}" y="31.25" width="{830-60-x1:.1f}" height="1.5" fill="url(#r)"/>'
            f'<rect x="{x0-4:.1f}" y="28" width="8" height="8" rx="1.5" transform="rotate(45 {x0:.1f} 32)" class="gold"/>'
            f'<rect x="{x1-4:.1f}" y="28" width="8" height="8" rx="1.5" transform="rotate(45 {x1:.1f} 32)" class="gold"/>'
            f'<text x="415" y="42" text-anchor="middle" class="serif ink" font-size="27" font-weight="600" letter-spacing=".4" '
            f'textLength="{tw:.1f}" lengthAdjust="spacing">{esc(title)}</text>')
    return _svg(w, h, title, body, defs)


def _chip(x, y, label, cls, size=13.5, h=30):
    tw = est(label, size)
    w = tw + 40
    return (w, f'<g><rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" class="tile"/>'
                f'<circle cx="{x+16:.1f}" cy="{y+h/2}" r="3.6" class="{cls}"/>'
                f'<text x="{x+29:.1f}" y="{y+h/2+4.8:.1f}" class="sans ink" font-size="{size}" font-weight="500" '
                f'textLength="{tw:.1f}" lengthAdjust="spacing">{esc(label)}</text></g>')


def toolkit():
    groups = [("Languages", ["Python", "HTML5", "CSS", "C++"]), ("AI / ML", ["PyTorch", "TensorFlow"]),
              ("Cloud", ["AWS"]), ("Tools", ["GitHub", "Kaggle"]), ("Design", ["Canva"]), ("Web / API", ["Flask API"])]
    cw, ch, gx, gy = 407, 92, 16, 14
    W = 2 * cw + gx
    H = 3 * ch + 2 * gy
    body, k = [], 0
    for gi, (name, items) in enumerate(groups):
        cx = (gi % 2) * (cw + gx); cy = (gi // 2) * (ch + gy)
        body.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="20" class="tile"/>')
        body.append(f'<text x="{cx+24}" y="{cy+34}" class="serif muted" font-size="17" font-style="italic">{esc(name)}</text>')
        x = cx + 24
        for it in items:
            w, s = _chip(x, cy + 46, it, DOT_CLASSES[k % 5]); k += 1
            body.append(s); x += w + 10
    return _svg(W, H, "Tech stack", "".join(body), desc="Languages: Python, HTML5, CSS, C++. AI/ML: PyTorch, TensorFlow. Cloud: AWS. Tools: GitHub, Kaggle. Design: Canva. Web/API: Flask API.")


def fields(items):
    maxw, size, h, gap = 800, 14.5, 34, 12
    rows, cur, curw = [], [], 0
    for it in items:
        w = est(it, size) + 40
        if cur and curw + gap + w > maxw:
            rows.append((cur, curw)); cur, curw = [], 0
        cur.append((it, w)); curw += (gap if cur[:-1] else 0) + w
    if cur:
        rows.append((cur, curw))
    W = 830
    H = len(rows) * (h + gap) - gap + 4
    body, k = [], 0
    for ri, (row, rw) in enumerate(rows):
        x = (W - rw) / 2
        y = 2 + ri * (h + gap)
        for it, w in row:
            _, s = _chip(x, y, it, DOT_CLASSES[k % 5], size=size, h=h); k += 1
            body.append(s); x += w + gap
    return _svg(W, H, "Primary fields", "".join(body), desc=", ".join(items))


GH = ("M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z")


def button(kind):
    w, h = 330, 56
    if kind == "email":
        label, icon, title = EMAIL, '<rect x="-8" y="-6" width="16" height="12" rx="2.5" fill="none" stroke="#fff" stroke-width="1.6"/><path d="M-7 -4.5L0 1.2 7 -4.5" fill="none" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/>', "Email"
    else:
        label, icon, title = f"github.com/{USER}", f'<path transform="translate(-8 -8)" fill="#fff" d="{GH}"/>', "GitHub"
    tw = est(label, 15)
    defs = ('<linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8f74d8"/><stop offset="1" stop-color="#e58ab3"/></linearGradient>')
    body = (f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{h/2-1}" class="tile"/>'
            f'<circle cx="30" cy="{h/2}" r="18" fill="url(#b)"/><g transform="translate(30 {h/2})">{icon}</g>'
            f'<text x="62" y="{h/2+5}" class="sans ink" font-size="15" font-weight="500" textLength="{tw:.1f}" lengthAdjust="spacing">{esc(label)}</text>')
    return _svg(w, h, f"{title}: {label}", body, defs)


def footer(quote_lines):
    W, H = 830, 200
    def wave(y, amp, phase):
        def p(a, ph):
            return (f"M0 {y} C138 {y-a} 277 {y+a} 415 {y} S692 {y-a} 830 {y} V{H} H0 Z" if ph == 0 else
                    f"M0 {y} C138 {y+a} 277 {y-a} 415 {y} S692 {y+a} 830 {y} V{H} H0 Z")
        return p(amp, phase), p(amp, 1 - phase)
    layers = []
    for (y, amp, ph, cls, op, dur) in [(156, 15, 0, "lav", .34, 13), (168, 13, 1, "pink", .30, 17), (181, 11, 0, "gold", .28, 21)]:
        a, b = wave(y, amp, ph)
        layers.append(f'<path d="{a}" class="{cls}" fill-opacity="{op}"><animate attributeName="d" values="{a};{b};{a}" dur="{dur}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/></path>')
    q = "".join(f'<text x="415" y="{58 + i*30}" text-anchor="middle" class="serif ink" font-size="21" font-style="italic">{esc(l)}</text>' for i, l in enumerate(quote_lines))
    year = datetime.date.today().year
    body = (f'<rect x="{415-4}" y="10" width="8" height="8" rx="1.5" transform="rotate(45 415 14)" class="gold"/>{q}'
            f'<text x="415" y="128" text-anchor="middle" class="sans muted" font-size="12.5">© {year} {esc(NAME)}</text>{"".join(layers)}')
    return _svg(W, H, "Footer quote", body, desc=" ".join(quote_lines))
