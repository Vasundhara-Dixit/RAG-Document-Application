"""Animated hero banner (dark + light). Pure SVG + SMIL + CSS. No JavaScript."""
import random
from common import NAME, SERIF, SANS, MONO, esc

W, H = 1280, 740
FX, FY, FW, FH = 800, 44, 436, 654          # portrait frame (2:3)

DARK = dict(
    mode="dark", bg0="#120d1c", bg1="#1b1330", bg2="#2a1a3f",
    glowA="#a98bef", glowB="#f5a9cb", glowC="#ffe9a3",
    ink="#f6f0ff", muted="#bcaedb", faint="#8f80b3",
    lav="#cbb8ff", pink="#ffb8d6", cream="#fff0b8", emerald="#6fe0b0", gold="#e9cf8f",
    glass="#ffffff", glass_op=0.055, stroke="#cbb8ff", stroke_op=0.30,
    term="#0d0816", term_op=0.55, grid_op=0.10, particle="#ffffff",
    name_a="#d8c8ff", name_b="#ffc0da", name_c="#fff0b8", tint_a="#b79cf2", tint_b="#f5a9cb",
)
LIGHT = dict(
    mode="light", bg0="#fbf8ff", bg1="#fff3f8", bg2="#fff8e2",
    glowA="#b9a0f5", glowB="#fbbcd5", glowC="#ffe08a",
    ink="#2a1f45", muted="#5a4c7d", faint="#8a7ca8",
    lav="#6c4dc4", pink="#c93d78", cream="#8a6410", emerald="#12805a", gold="#94701a",
    glass="#ffffff", glass_op=0.66, stroke="#8f74d8", stroke_op=0.38,
    term="#ffffff", term_op=0.72, grid_op=0.13, particle="#8f74d8",
    name_a="#5636a8", name_b="#c93d78", name_c="#a4781a", tint_a="#b79cf2", tint_b="#f5a9cb",
)

ROLES = ["Data Analyst", "Python Developer", "Agentic AI Developer", "AI/ML Engineer",
         "AI Innovator", "Healthcare-Tech Creator", "Creative Technologist", "Tech Builder"]
FOCUS = ["agentic AI", "data analytics", "computer vision", "healthcare tech"]
TICKER = ("Python  ·  PyTorch  ·  TensorFlow  ·  AWS  ·  Flask API  ·  Kaggle  ·  "
          "Computer Vision  ·  Healthcare Tech  ·  Data Analytics  ·  ")

CW = 9.0  # terminal glyph advance at 15px (forced with textLength so it is font-independent)


def _slots(i, n, fade, extra_vals=(0, 1, 1, 0)):
    """keyTimes/values for slot i of n in a looping cycle: fade in, hold, fade out."""
    s, e = i / n, (i + 1) / n
    kt = [0.0]
    vals = [extra_vals[3] if i > 0 else 0]
    def add(t, v):
        if t <= kt[-1]:
            t = min(kt[-1] + 1e-4, 1.0)
        kt.append(round(t, 5)); vals.append(v)
    if i > 0:
        add(s, 0)
    add(s + fade, 1)
    add(e - fade, 1)
    add(e, 0)
    if kt[-1] < 1.0:
        kt.append(1.0); vals.append(0)
    return kt, vals


def typed_line(idx, text, x, y, t0, dt, color_prompt, color_text, final, P):
    n = len(text)
    vals = ";".join(f"{CW*k:.1f}" for k in range(n + 1))
    xs = ";".join(f"{x + CW*k:.1f}" for k in range(n + 1))
    kt = ";".join(f"{k/(n+1):.5f}" for k in range(n + 1))
    dur = (n + 1) * dt
    cid = f"tl{idx}"
    clip = (f'<clipPath id="{cid}"><rect x="{x}" y="{y-15}" width="0" height="21">'
            f'<animate attributeName="width" calcMode="discrete" values="{vals}" keyTimes="{kt}" '
            f'dur="{dur:.3f}s" begin="{t0:.3f}s" fill="freeze"/></rect></clipPath>')
    prompt, rest = text[0], text[1:]
    txt = (f'<text x="{x}" y="{y}" class="mono" font-size="15" textLength="{n*CW:.1f}" lengthAdjust="spacing" '
           f'clip-path="url(#{cid})" xml:space="preserve"><tspan fill="{color_prompt}">{esc(prompt)}</tspan>'
           f'<tspan fill="{color_text}">{esc(rest)}</tspan></text>')
    cur = (f'<rect x="{x}" y="{y-13}" width="8" height="17" rx="1.5" fill="{P["pink"]}" opacity="0">'
           f'<set attributeName="opacity" to="1" begin="{t0:.3f}s"/>'
           f'<animate attributeName="x" calcMode="discrete" values="{xs}" keyTimes="{kt}" dur="{dur:.3f}s" '
           f'begin="{t0:.3f}s" fill="freeze"/>')
    if final:
        cur += (f'<animate attributeName="opacity" calcMode="discrete" values="1;0" keyTimes="0;0.5" dur="1.1s" '
                f'begin="{t0+dur:.3f}s" repeatCount="indefinite"/>')
    else:
        cur += f'<set attributeName="opacity" to="0" begin="{t0+dur:.3f}s"/>'
    cur += '</rect>'
    return clip, txt + cur, t0 + dur


def build_banner(P, b64_png):
    rnd = random.Random(11)
    defs, body = [], []
    light = P["mode"] == "light"

    # ---------- defs ----------
    defs.append(f'''
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{P['bg0']}"/><stop offset=".55" stop-color="{P['bg1']}"/><stop offset="1" stop-color="{P['bg2']}"/></linearGradient>
<radialGradient id="gA"><stop offset="0" stop-color="{P['glowA']}" stop-opacity="{.5 if not light else .55}"/><stop offset="1" stop-color="{P['glowA']}" stop-opacity="0"/></radialGradient>
<radialGradient id="gB"><stop offset="0" stop-color="{P['glowB']}" stop-opacity="{.42 if not light else .6}"/><stop offset="1" stop-color="{P['glowB']}" stop-opacity="0"/></radialGradient>
<radialGradient id="gC"><stop offset="0" stop-color="{P['glowC']}" stop-opacity="{.20 if not light else .55}"/><stop offset="1" stop-color="{P['glowC']}" stop-opacity="0"/></radialGradient>
<linearGradient id="nameG" gradientUnits="userSpaceOnUse" x1="64" y1="0" x2="700" y2="0"><stop offset="0" stop-color="{P['name_a']}"/><stop offset=".55" stop-color="{P['name_b']}"/><stop offset="1" stop-color="{P['name_c']}"/></linearGradient>
<linearGradient id="barG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{P['lav']}"/><stop offset=".6" stop-color="{P['pink']}"/><stop offset="1" stop-color="{P['gold']}"/></linearGradient>
<linearGradient id="frameG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{P['lav']}"/><stop offset=".5" stop-color="{P['pink']}"/><stop offset="1" stop-color="{P['gold']}"/></linearGradient>
<linearGradient id="tint" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{P['tint_a']}"/><stop offset="1" stop-color="{P['tint_b']}"/></linearGradient>
<linearGradient id="trail" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".85" stop-color="{P['lav'] if not light else '#ffffff'}" stop-opacity=".30"/><stop offset="1" stop-color="#ffffff" stop-opacity=".75"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".95"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<radialGradient id="maskG" cx=".5" cy=".5" r=".6"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
<linearGradient id="tickM" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000"/><stop offset=".06" stop-color="#fff"/><stop offset=".94" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
<mask id="gridMask"><rect width="{W}" height="{H}" fill="url(#maskG)"/></mask>
<mask id="tickMask"><rect x="330" y="606" width="378" height="46" fill="url(#tickM)"/></mask>
<pattern id="grid" width="56" height="56" patternUnits="userSpaceOnUse"><path d="M56 0H0V56" fill="none" stroke="{P['lav']}" stroke-width="1"/></pattern>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff"/></pattern>
<pattern id="fgrid" width="32" height="32" patternUnits="userSpaceOnUse" x="{FX}" y="{FY}"><path d="M32 0H0V32" fill="none" stroke="{P['lav']}" stroke-width=".8"/></pattern>
<filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="16"/></filter>
<filter id="shadow" x="-20%" y="-10%" width="140%" height="130%"><feGaussianBlur stdDeviation="22"/></filter>
<clipPath id="frameClip"><rect x="{FX}" y="{FY}" width="{FW}" height="{FH}" rx="26"/></clipPath>
<clipPath id="revealClip"><rect x="{FX}" y="{FY}" width="{FW}" height="0"><animate attributeName="height" values="0;{FH}" keyTimes="0;1" calcMode="spline" keySplines=".45 0 .25 1" dur="2.6s" begin="1.2s" fill="freeze"/></rect></clipPath>
<clipPath id="tickClip"><rect x="330" y="606" width="378" height="46"/></clipPath>
''')

    # ---------- atmosphere ----------
    body.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    body.append(f'''<g class="fx">
<circle cx="180" cy="130" r="380" fill="url(#gA)"><animateTransform attributeName="transform" type="translate" values="0 0;46 -24;-18 34;0 0" dur="26s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.33;.66;1" keySplines=".45 0 .55 1;.45 0 .55 1;.45 0 .55 1"/></circle>
<circle cx="1040" cy="620" r="360" fill="url(#gB)"><animateTransform attributeName="transform" type="translate" values="0 0;-40 26;30 -30;0 0" dur="30s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.33;.66;1" keySplines=".45 0 .55 1;.45 0 .55 1;.45 0 .55 1"/></circle>
<circle cx="560" cy="700" r="300" fill="url(#gC)"><animateTransform attributeName="transform" type="translate" values="0 0;30 -20;-26 12;0 0" dur="24s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.33;.66;1" keySplines=".45 0 .55 1;.45 0 .55 1;.45 0 .55 1"/></circle>
</g>''')
    body.append(f'<rect width="{W}" height="{H}" fill="url(#grid)" opacity="{P["grid_op"]}" mask="url(#gridMask)"/>')
    parts = ['<g class="fx">']
    cols = [P["particle"], P["lav"], P["pink"], P["cream"]]
    for i in range(30):
        cx, cy = rnd.uniform(20, W - 20), rnd.uniform(120, H + 40)
        r = rnd.choice([1.2, 1.6, 2.0, 2.6])
        dur = rnd.uniform(14, 28)
        begin = -rnd.uniform(0, dur)
        dx = rnd.uniform(-30, 30)
        op = rnd.uniform(.35, .8) if not light else rnd.uniform(.25, .55)
        parts.append(
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r}" fill="{rnd.choice(cols)}" opacity="0">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{dx:.0f} -170" dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;{op:.2f};0" keyTimes="0;.5;1" dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/></circle>')
    parts.append('</g>')
    body.append("".join(parts))

    # ---------- terminal window ----------
    tx, ty, tw, th = 64, 56, 660, 212
    body.append(f'''<g>
<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="18" fill="{P['term']}" fill-opacity="{P['term_op']}" stroke="{P['stroke']}" stroke-opacity="{P['stroke_op']}"/>
<rect x="{tx}" y="{ty}" width="{tw}" height="40" rx="18" fill="{P['glass']}" fill-opacity="{P['glass_op']*0.7:.3f}"/>
<line x1="{tx}" y1="{ty+40}" x2="{tx+tw}" y2="{ty+40}" stroke="{P['stroke']}" stroke-opacity="{P['stroke_op']*0.7:.2f}"/>
<circle cx="{tx+26}" cy="{ty+20}" r="5.5" fill="{P['pink']}"/><circle cx="{tx+46}" cy="{ty+20}" r="5.5" fill="{'#f0c96a' if light else P['cream']}"/><circle cx="{tx+66}" cy="{ty+20}" r="5.5" fill="{P['emerald']}"/>
<text x="{tx+92}" y="{ty+25}" class="mono" font-size="12.5" fill="{P['faint']}">vasundhara@workspace ~ zsh</text>
</g>''')
    lines = [
        ("$ whoami", "cmd"),
        ("› Vasundhara Dixit · data analyst · python dev · agentic AI", "out"),
        ("$ cat mission.txt", "cmd"),
        ("› turn messy data into decisions, models into meaning", "out"),
        ("$ status --now", "cmd"),
        ("› building with intelligence, creating with purpose", "out"),
    ]
    t = 0.55
    clips, texts = [], []
    for i, (txt, kind) in enumerate(lines):
        y = ty + 76 + i * 25
        dt = 0.06 if kind == "cmd" else 0.017
        c_prompt = P["pink"] if kind == "cmd" else P["emerald"]
        c_text = P["ink"] if kind == "cmd" else P["lav"]
        clip, tx_svg, t_end = typed_line(i, txt, tx + 26, y, t, dt, c_prompt, c_text, i == len(lines) - 1, P)
        clips.append(clip); texts.append(tx_svg)
        t = t_end + 0.28
    defs.append("".join(clips))
    body.append("<g>" + "".join(texts) + "</g>")

    # ---------- name ----------
    ny = 372
    body.append(f'''<g opacity="0"><animate attributeName="opacity" values="0;1" dur="1.3s" begin="0.9s" fill="freeze"/>
<animateTransform attributeName="transform" type="translate" values="0 16;0 0" keyTimes="0;1" calcMode="spline" keySplines=".2 .7 .2 1" dur="1.3s" begin="0.9s" fill="freeze"/>
<text x="64" y="{ny}" font-family="{SERIF}" font-size="74" font-weight="700" fill="{P['glowB']}" opacity="{.35 if not light else .22}" filter="url(#soft)" letter-spacing="-1">{NAME}</text>
<text x="64" y="{ny}" font-family="{SERIF}" font-size="74" font-weight="700" fill="url(#nameG)" letter-spacing="-1">{NAME}</text>
</g>''')

    # ---------- role cycler ----------
    ry = 452
    n = len(ROLES)
    slot = 2.6
    total = slot * n
    fade = 0.42 / total
    role_svg = []
    for i, role in enumerate(ROLES):
        kt, vals = _slots(i, n, fade)
        kts = ";".join(str(k) for k in kt)
        ov = ";".join(str(v) for v in vals)
        yv = ";".join({0: "0 12", 1: "0 0"}[v] if j < len(vals) and (v == 1 or (j <= vals.index(1))) else "0 -12"
                      for j, v in enumerate(vals))
        # explicit slide values: below before/at entry, centre while visible, above after exit
        first1 = vals.index(1)
        last1 = len(vals) - 1 - vals[::-1].index(1)
        yv = ";".join("0 12" if j < first1 else ("0 0" if j <= last1 else "0 -12") for j in range(len(vals)))
        role_svg.append(
            f'<g opacity="0"><animate attributeName="opacity" values="{ov}" keyTimes="{kts}" dur="{total:.1f}s" begin="3.4s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" values="{yv}" keyTimes="{kts}" dur="{total:.1f}s" begin="3.4s" repeatCount="indefinite"/>'
            f'<text x="86" y="{ry}" font-family="{SANS}" font-size="34" font-weight="500" fill="{P["ink"]}" letter-spacing=".2">{esc(role)}</text></g>')
    dots = []
    for i in range(n):
        kt, vals = _slots(i, n, fade)
        kts = ";".join(str(k) for k in kt)
        ov = ";".join(("1" if v == 1 else ".28") for v in vals)
        rv = ";".join(("4.2" if v == 1 else "2.6") for v in vals)
        dots.append(f'<circle cx="{88 + i*17}" cy="{ry+30}" r="2.6" fill="{P["pink"] if light else P["lav"]}" opacity="0">'
                    f'<animate attributeName="opacity" values="{ov}" keyTimes="{kts}" dur="{total:.1f}s" begin="3.4s" repeatCount="indefinite"/>'
                    f'<animate attributeName="r" values="{rv}" keyTimes="{kts}" dur="{total:.1f}s" begin="3.4s" repeatCount="indefinite"/></circle>')
    body.append(f'''<g>
<rect x="64" y="{ry-34}" width="3" height="58" rx="1.5" fill="url(#barG)" opacity="0"><animate attributeName="opacity" values="0;1" dur=".8s" begin="3.2s" fill="freeze"/></rect>
{"".join(role_svg)}{"".join(dots)}
</g>''')
    body.append(f'''<text x="64" y="{ry+92}" font-family="{SERIF}" font-style="italic" font-size="19" fill="{P['muted']}" opacity="0">
Build with intelligence, create with purpose.<animate attributeName="opacity" values="0;1" dur="1.2s" begin="4s" fill="freeze"/></text>''')

    # ---------- status strip ----------
    sx, sy, sw, sh = 64, 600, 660, 56
    fslot = 3.0
    ftotal = fslot * len(FOCUS)
    focus_svg = []
    for i, f in enumerate(FOCUS):
        kt, vals = _slots(i, len(FOCUS), 0.35 / ftotal)
        kts = ";".join(str(k) for k in kt); ov = ";".join(str(v) for v in vals)
        focus_svg.append(f'<text x="{sx+50}" y="{sy+34}" class="mono" font-size="13.5" fill="{P["ink"]}" opacity="0">focus · {esc(f)}'
                         f'<animate attributeName="opacity" values="{ov}" keyTimes="{kts}" dur="{ftotal:.1f}s" begin="4.4s" repeatCount="indefinite"/></text>')
    tk_w = len(TICKER) * 7.8
    body.append(f'''<g>
<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="16" fill="{P['glass']}" fill-opacity="{P['glass_op']}" stroke="{P['stroke']}" stroke-opacity="{P['stroke_op']}"/>
<circle cx="{sx+28}" cy="{sy+28}" r="4.5" fill="{P['emerald']}"/>
<circle cx="{sx+28}" cy="{sy+28}" r="4.5" fill="none" stroke="{P['emerald']}" stroke-width="1.5"><animate attributeName="r" values="4.5;15" dur="2.4s" repeatCount="indefinite"/><animate attributeName="opacity" values=".7;0" dur="2.4s" repeatCount="indefinite"/></circle>
{"".join(focus_svg)}
<line x1="{sx+250}" y1="{sy+14}" x2="{sx+250}" y2="{sy+sh-14}" stroke="{P['stroke']}" stroke-opacity=".3"/>
<g mask="url(#tickMask)"><g clip-path="url(#tickClip)"><g>
<animateTransform attributeName="transform" type="translate" values="0 0;{-tk_w:.0f} 0" dur="34s" repeatCount="indefinite"/>
<text x="{sx+284}" y="{sy+34}" class="mono" font-size="13" fill="{P['muted']}" textLength="{tk_w:.0f}" lengthAdjust="spacing" xml:space="preserve">{esc(TICKER)}</text>
<text x="{sx+284+tk_w:.0f}" y="{sy+34}" class="mono" font-size="13" fill="{P['muted']}" textLength="{tk_w:.0f}" lengthAdjust="spacing" xml:space="preserve">{esc(TICKER)}</text>
</g></g></g>
</g>''')

    # ---------- portrait frame ----------
    cxm, cym = FX + FW / 2, FY + FH / 2
    edge_dur, edge_begin = 2.6, 1.2
    rep_begin = edge_begin + edge_dur + 3.0
    body.append(f'''<g>
<rect x="{FX+10}" y="{FY+24}" width="{FW}" height="{FH}" rx="26" fill="{P['glowB'] if not light else P['glowA']}" opacity="{.20 if not light else .18}" filter="url(#shadow)"><animate attributeName="opacity" values="{.16 if not light else .14};{.34 if not light else .28};{.16 if not light else .14}" dur="7s" repeatCount="indefinite"/></rect>
<rect x="{FX}" y="{FY}" width="{FW}" height="{FH}" rx="26" fill="{P['glass']}" fill-opacity="{P['glass_op']}"/>
<g clip-path="url(#frameClip)">
  <rect x="{FX}" y="{FY}" width="{FW}" height="{FH}" fill="url(#fgrid)" opacity=".28"/>
  <g clip-path="url(#revealClip)">
    <g transform="translate({cxm} {cym})"><g>
      <animateTransform attributeName="transform" type="scale" values="1;1.035;1" dur="24s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/>
      <image x="{-FW/2}" y="{-FH/2}" width="{FW}" height="{FH}" preserveAspectRatio="xMidYMid slice" xlink:href="data:image/png;base64,{b64_png}"/>
    </g></g>
    <rect x="{FX}" y="{FY}" width="{FW}" height="{FH}" fill="url(#tint)" opacity=".34"><animate attributeName="opacity" values=".34;.06" dur="2.2s" begin="{edge_begin+edge_dur}s" fill="freeze"/></rect>
    <rect x="{FX}" y="{FY}" width="{FW}" height="{FH}" fill="url(#scan)" opacity=".20"><animate attributeName="opacity" values=".20;.045" dur="2.2s" begin="{edge_begin+edge_dur}s" fill="freeze"/></rect>
  </g>
  <g opacity="1">
    <rect x="{FX}" y="{FY-90}" width="{FW}" height="90" fill="url(#trail)"><animate attributeName="y" values="{FY-90};{FY+FH-90}" keyTimes="0;1" calcMode="spline" keySplines=".45 0 .25 1" dur="{edge_dur}s" begin="{edge_begin}s" fill="freeze"/><set attributeName="opacity" to="0" begin="{edge_begin+edge_dur}s"/></rect>
    <rect x="{FX}" y="{FY-1.5}" width="{FW}" height="3" fill="url(#edge)"><animate attributeName="y" values="{FY-1.5};{FY+FH-1.5}" keyTimes="0;1" calcMode="spline" keySplines=".45 0 .25 1" dur="{edge_dur}s" begin="{edge_begin}s" fill="freeze"/><set attributeName="opacity" to="0" begin="{edge_begin+edge_dur}s"/></rect>
  </g>
  <g>
    <rect x="{FX}" y="{FY-140}" width="{FW}" height="140" fill="url(#trail)" opacity="0"><animate attributeName="y" values="{FY-140};{FY+FH};{FY+FH}" keyTimes="0;.34;1" calcMode="spline" keySplines=".4 0 .2 1;0 0 1 1" dur="9s" begin="{rep_begin}s" repeatCount="indefinite"/><animate attributeName="opacity" values="0;.85;.85;0;0" keyTimes="0;.03;.3;.34;1" dur="9s" begin="{rep_begin}s" repeatCount="indefinite"/></rect>
    <rect x="{FX}" y="{FY-1.5}" width="{FW}" height="3" fill="url(#edge)" opacity="0"><animate attributeName="y" values="{FY-1.5};{FY+FH-1.5};{FY+FH-1.5}" keyTimes="0;.34;1" calcMode="spline" keySplines=".4 0 .2 1;0 0 1 1" dur="9s" begin="{rep_begin}s" repeatCount="indefinite"/><animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.03;.3;.34;1" dur="9s" begin="{rep_begin}s" repeatCount="indefinite"/></rect>
    <rect x="{FX-260}" y="{FY}" width="220" height="{FH}" fill="url(#sheen)" transform="skewX(-14)" opacity="0"><animate attributeName="x" values="{FX-260};{FX+FW+120}" keyTimes="0;1" dur="1.8s" begin="{rep_begin+1.0}s;{rep_begin+1.0+9}s" fill="freeze"/><set attributeName="opacity" to="1" begin="{rep_begin+1.0}s"/></rect>
  </g>
</g>
<rect x="{FX}" y="{FY}" width="{FW}" height="{FH}" rx="26" fill="none" stroke="url(#frameG)" stroke-width="1.6" stroke-opacity=".85"/>
<g fill="none" stroke="{P['gold']}" stroke-width="2" stroke-linecap="round" opacity=".9">
<path d="M{FX-10} {FY+34}V{FY-10}H{FX+34}"/><path d="M{FX+FW+10} {FY+34}V{FY-10}H{FX+FW-34}"/>
<path d="M{FX-10} {FY+FH-34}V{FY+FH+10}H{FX+34}"/><path d="M{FX+FW+10} {FY+FH-34}V{FY+FH+10}H{FX+FW-34}"/>
</g>
</g>''')

    title = f"{NAME} — Data Analyst, Python Developer, Agentic AI Developer"
    desc = ("Animated profile banner. A terminal types out an introduction, a holographic scan reveals a portrait "
            "of Vasundhara Dixit at her workspace, and her role cycles between Data Analyst, Python Developer, "
            "Agentic AI Developer, AI/ML Engineer, AI Innovator, Healthcare-Tech Creator, Creative Technologist and Tech Builder.")
    css = f".mono{{font-family:{MONO}}}@media (prefers-reduced-motion:reduce){{.fx{{display:none}}}}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}" role="img" aria-labelledby="t d"><title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
            f'<style>{css}</style><defs>{"".join(defs)}</defs>{"".join(body)}</svg>')
