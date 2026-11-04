"""Introduction scene (text card + swinging ID badge in ONE svg) and the Interests card. Dark + light builds."""
from common import NAME, SERIF, SANS, MONO, esc
from static_parts import est
from lanyard import lanyard_parts, VW as LW, VH as LH

PAL = {
    "dark": dict(bg0="#160f24", bg1="#221636", ink="#f6f0ff", muted="#cfc3ea", faint="#9a8bbd", lav="#cbb8ff",
                 pink="#ffb8d6", gold="#e9cf8f", line="#cbb8ff", line_op=".30", tile="#ffffff", tile_op=".05",
                 name0="#d8c8ff", name1="#ffc0da"),
    "light": dict(bg0="#fbf8ff", bg1="#fff1f8", ink="#2a1f45", muted="#4b3d70", faint="#7d6fa0", lav="#6c4dc4",
                  pink="#c93d78", gold="#94701a", line="#8f74d8", line_op=".38", tile="#ffffff", tile_op=".72",
                  name0="#4a2f9a", name1="#c93d78"),
}


def wrap(tokens, size, maxw, fudge=1.1):
    """tokens = [(word, cls)]; returns lines, each a list of (word, cls). Width is a safe over-estimate."""
    lines, cur, w = [], [], 0.0
    sp = est(" ", size) * fudge
    for word, cls in tokens:
        ww = est(word, size) * fudge
        if cur and w + sp + ww > maxw:
            lines.append(cur); cur, w = [], 0.0
        w += (sp if cur else 0) + ww
        cur.append((word, cls))
    if cur:
        lines.append(cur)
    return lines


def tok(text, cls=None):
    return [(w, cls) for w in text.split()]


def render_lines(lines, x, y, lh, base_attrs):
    out = []
    for i, ln in enumerate(lines):
        parts = []
        for j, (word, cls) in enumerate(ln):
            sep = " " if j else ""
            parts.append(f'{sep}<tspan class="{cls}">{esc(word)}</tspan>' if cls else f"{sep}{esc(word)}")
        out.append(f'<text x="{x}" y="{y + i * lh}" {base_attrs}>{"".join(parts)}</text>')
    return "".join(out), y + (len(lines) - 1) * lh


def build_intro_scene(photo_b64, mode, badge=True):
    P = PAL[mode]
    CW = 508                       # text card width
    W, H = (830 if badge else CW + 2), 612
    s = LW and 300 / LW            # badge scale -> 300px wide
    px = 24                        # inner padding
    maxw = CW - 2 * px - 8

    css = (f".sa{{font-family:{SANS}}}.se{{font-family:{SERIF}}}"
           f".k{{fill:{P['lav']};font-weight:600}}.kp{{fill:{P['pink']};font-weight:600}}")

    body = []
    # card
    body.append(f'<rect x="1" y="14" width="{CW}" height="{H-28}" rx="22" fill="url(#ibg)" stroke="{P["line"]}" stroke-opacity="{P["line_op"]}"/>')
    body.append(f'<rect x="{px}" y="14" width="{CW-2*px}" height="2" rx="1" fill="url(#iline)"/>')

    y = 72
    body.append(f'<text x="{px+2}" y="{y}" class="se" font-size="23" font-style="italic" fill="{P["muted"]}">Hello, I’m</text>')
    y += 48
    body.append(f'<text x="{px}" y="{y}" class="se" font-size="45" font-weight="700" fill="url(#iname)" letter-spacing="-.5">{esc(NAME)}</text>')
    y += 34
    lead = wrap(tok("a data analyst, Python developer and agentic-AI developer."), 17.5, maxw)
    t, yl = render_lines(lead, px + 2, y, 25, f'class="sa" font-size="17.5" font-weight="500" fill="{P["ink"]}"')
    body.append(t)
    y = yl + 22
    body.append(f'<rect x="{px+2}" y="{y}" width="56" height="3" rx="1.5" fill="url(#iline)"/>')
    y += 34

    p2 = wrap(tok("I build AI-powered solutions where intelligence meets creativity: turning data into decisions, "
                  "teaching machines to see through") + tok("computer vision,", "kp")
              + tok("and shaping technology that can make") + tok("healthcare", "kp") + tok("better."), 15, maxw)
    t, yl = render_lines(p2, px + 2, y, 24, f'class="sa" font-size="15" fill="{P["muted"]}"')
    body.append(t)
    y = yl + 30

    p3 = wrap(tok("My everyday toolkit is") + tok("Python,", "k") + tok("PyTorch", "k") + tok("and") + tok("TensorFlow,", "k")
              + tok("with") + tok("AWS", "k") + tok("for the cloud and") + tok("Flask", "k")
              + tok("for APIs. Beyond the code, I’m a creative technologist who designs with Canva and treats every "
                    "project as a chance to build something meaningful."), 15, maxw)
    t, yl = render_lines(p3, px + 2, y, 24, f'class="sa" font-size="15" fill="{P["muted"]}"')
    body.append(t)
    y = yl + 34

    q = wrap(tok("Build with intelligence, create with purpose, and let technology become an extension of your creativity."),
             18.5, maxw - 30)
    qh = len(q) * 28 + 22
    body.append(f'<rect x="{px+2}" y="{y-6}" width="{CW-2*px-4}" height="{qh}" rx="14" fill="{P["tile"]}" fill-opacity="{P["tile_op"]}" '
                f'stroke="{P["line"]}" stroke-opacity="{P["line_op"]*1 if False else .25}"/>')
    body.append(f'<rect x="{px+2}" y="{y-6}" width="4" height="{qh}" rx="2" fill="url(#iline)"/>')
    t, yl = render_lines(q, px + 24, y + 22, 28, f'class="se" font-size="18.5" font-style="italic" fill="{P["ink"]}"')
    body.append(t)
    need = yl + 36
    if need > H - 14:
        raise SystemExit(f"intro text overflows its card: needs {need}, has {H-14}")

    ldefs, lbody = ("", "")
    if badge:
        ldefs, lbody, _ = lanyard_parts(photo_b64, mode)
    defs = (f'<linearGradient id="ibg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{P["bg0"]}"/><stop offset="1" stop-color="{P["bg1"]}"/></linearGradient>'
            f'<linearGradient id="iline" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{P["lav"]}"/><stop offset=".6" stop-color="{P["pink"]}"/><stop offset="1" stop-color="{P["gold"]}"/></linearGradient>'
            f'<linearGradient id="iname" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{P["name0"]}"/><stop offset="1" stop-color="{P["name1"]}"/></linearGradient>'
            + ldefs)
    badge_x = W - LW * s - 2
    alt = ("Hello, I’m Vasundhara Dixit, a data analyst, Python developer and agentic-AI developer. "
           "I build AI-powered solutions where intelligence meets creativity: turning data into decisions, teaching machines "
           "to see through computer vision, and shaping technology that can make healthcare better. My everyday toolkit is "
           "Python, PyTorch and TensorFlow, with AWS for the cloud and Flask for APIs. Beyond the code, I’m a creative "
           "technologist who designs with Canva and treats every project as a chance to build something meaningful.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'role="img" aria-labelledby="t d"><title id="t">Introduction — {esc(NAME)}</title><desc id="d">{esc(alt)}</desc>'
            f'<style>{css}</style><defs>{defs}</defs>{"".join(body)}'
            + (f'<g transform="translate({badge_x:.1f} 0) scale({s:.5f})">{lbody}</g>' if badge else "") + '</svg>')


# ------------------------------------------------------------------------------------------------ interests
ICONS = {
    "agent":  '<g fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round"><path d="M0-8L-9 8M0-8L9 8M-9 8H9"/>'
              '<circle cx="0" cy="-9" r="3.6" fill="{c}"/><circle cx="-10" cy="8" r="3.6" fill="{c}"/><circle cx="10" cy="8" r="3.6" fill="{c}"/></g>',
    "health": '<g fill="none" stroke="{c}" stroke-width="3.4" stroke-linecap="round"><path d="M0-10V10M-10 0H10"/></g>',
    "vision": '<g fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round"><path d="M-12 0Q0-11 12 0Q0 11-12 0Z"/><circle r="3.8" fill="{c}"/></g>',
    "data":   '<g fill="{c}"><rect x="-10" y="1" width="5" height="9" rx="1.2"/><rect x="-2.5" y="-5" width="5" height="15" rx="1.2"/><rect x="5" y="-10" width="5" height="20" rx="1.2"/></g>',
    "create": '<g fill="{c}"><path d="M0-11C1.2-4 4-1.2 11 0 4 1.2 1.2 4 0 11-1.2 4-4 1.2-11 0-4-1.2-1.2-4 0-11Z"/></g>',
}
INTERESTS = [
    ("agent",  "Agentic AI",            "Autonomous systems that plan, reason and act toward a goal."),
    ("health", "Healthcare Technology", "Technology that helps people live healthier lives."),
    ("vision", "Computer Vision",       "Teaching machines to understand what they see."),
    ("data",   "Data Analytics",        "Turning raw data into clear, decision-ready insight."),
    ("create", "Creative Technology",   "Where design, art and code meet."),
]


def build_interests(mode):
    P = PAL[mode]
    W, cw, ch, gap = 830, 262, 172, 22
    css = f".sa{{font-family:{SANS}}}.se{{font-family:{SERIF}}}"
    cards = []
    for i, (ic, title, desc) in enumerate(INTERESTS):
        row, col = divmod(i, 3)
        n_in_row = 3 if row == 0 else 2
        x0 = (W - (n_in_row * cw + (n_in_row - 1) * gap)) / 2
        x, y = x0 + col * (cw + gap), 4 + row * (ch + gap)
        lines = wrap(tok(desc), 13.5, cw - 48, fudge=1.12)
        t, _ = render_lines(lines, x + 24, y + 124, 19, f'class="sa" font-size="13.5" fill="{P["muted"]}"')
        cards.append(
            f'<g><rect x="{x:.1f}" y="{y}" width="{cw}" height="{ch}" rx="18" fill="url(#cbg)" stroke="{P["line"]}" stroke-opacity="{P["line_op"]}"/>'
            f'<rect x="{x+24:.1f}" y="{y}" width="{cw-48}" height="2" rx="1" fill="url(#cl)"/>'
            f'<circle cx="{x+46:.1f}" cy="{y+46}" r="22" fill="{P["tile"]}" fill-opacity="{P["tile_op"]}" stroke="{P["line"]}" stroke-opacity=".28"/>'
            f'<g transform="translate({x+46:.1f} {y+46})">{ICONS[ic].format(c=P["lav"] if i % 2 == 0 else P["pink"])}</g>'
            f'<text x="{x+cw-24:.1f}" y="{y+40}" text-anchor="end" class="se" font-size="15" fill="{P["faint"]}" font-style="italic">0{i+1}</text>'
            f'<text x="{x+24:.1f}" y="{y+100}" class="se" font-size="20" font-weight="700" fill="{P["ink"]}">{esc(title)}</text>{t}</g>')
    H = 2 * ch + gap + 8
    defs = (f'<linearGradient id="cbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{P["bg0"]}"/><stop offset="1" stop-color="{P["bg1"]}"/></linearGradient>'
            f'<linearGradient id="cl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{P["lav"]}"/><stop offset=".6" stop-color="{P["pink"]}"/><stop offset="1" stop-color="{P["gold"]}"/></linearGradient>')
    alt = "Interests: " + "; ".join(f"{t} — {d}" for _, t, d in INTERESTS)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">'
            f'<title id="t">{esc(alt)}</title><style>{css}</style><defs>{defs}</defs>{"".join(cards)}</svg>')
