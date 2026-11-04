"""Swinging ID badge: drop -> decaying pendulum -> slow idle sway. Pure SVG + SMIL."""
import hashlib, random
import segno
from common import NAME, USER, GITHUB_URL, SERIF, SANS, MONO, esc

VW, VH = 440, 865

# Colour sets for the badge. The strap, metal clip and top band stay bright in both themes; the card body,
# text, name gradient, barcode and glow switch.
PAL = {
    "light": dict(card0="#ffffff", card1="#f4eeff", edge="#d9cdf7", glow="#6c4dc4", glow_op=".28",
                  name0="#4a2f9a", name1="#c93d78", role1="#5a4c7d", role2="#6c4dc4",
                  pill_f="#efe8ff", pill_s="#cdbdf5", pill_t="#3a2a66", div="#bfaeee",
                  bars="#2a1f45", scan="#6f6390", qr_edge="#e2d8fa", notch="#3a2a66"),
    "dark":  dict(card0="#2b1f47", card1="#1a1230", edge="#5b4796", glow="#cbb8ff", glow_op=".22",
                  name0="#d8c8ff", name1="#ffc0da", role1="#cfc3ea", role2="#cbb8ff",
                  pill_f="#3a2a5e", pill_s="#6a55a8", pill_t="#efe8ff", div="#7d68b8",
                  bars="#cbb8ff", scan="#a898cc", qr_edge="#4a3a7a", notch="#3a2a66"),
}
CX = 220
PIVOT = (CX, 0)


def qr_path(url, size, ox, oy, quiet=3):
    q = segno.make(url, error="m", boost_error=False)
    rows = [list(r) for r in q.matrix]
    m = len(rows)
    u = size / (m + 2 * quiet)
    d = []
    for y, row in enumerate(rows):
        x = 0
        while x < m:
            if row[x]:
                x0 = x
                while x < m and row[x]:
                    x += 1
                d.append(f"M{ox + (x0 + quiet) * u:.2f} {oy + (y + quiet) * u:.2f}h{(x - x0) * u:.2f}v{u:.2f}h-{(x - x0) * u:.2f}z")
            else:
                x += 1
    return "".join(d), m


def barcode(x, y, w, h, seed):
    rnd = random.Random(int(hashlib.sha1(seed.encode()).hexdigest()[:8], 16))
    bars, cx = [], 0
    while cx < w - 3:
        bw = rnd.choice([1, 1, 2, 2, 3, 4]); gap = rnd.choice([1, 2, 2, 3])
        if cx + bw > w:
            break
        bars.append(f'M{x + cx}  {y}h{bw}v{h}h-{bw}z'.replace("  ", " "))
        cx += bw + gap
    return "".join(bars)


def lanyard_parts(photo_b64, mode="light"):
    P = PAL[mode]
    y0 = 205                                 # card top
    cx = CX
    card_x, card_w = 60, 320
    photo_w, photo_h = 208, 260
    photo_x, photo_y = cx - photo_w / 2, y0 + 70
    name_y = photo_y + photo_h + 46
    role1_y, role2_y = name_y + 24, name_y + 44
    pill_y = role2_y + 16
    div_y = pill_y + 46
    band_y = div_y + 14
    qr_size = 124
    card_h = (band_y + qr_size + 20) - y0

    path, mods = qr_path(GITHUB_URL, qr_size, card_x + card_w - qr_size - 18, band_y)
    bars = barcode(card_x + 24, band_y + 10, 128, 58, NAME)

    drop = ('<animateTransform attributeName="transform" type="translate" calcMode="spline" '
            'values="0 -900;0 26;0 -9;0 0" keyTimes="0;.62;.82;1" keySplines=".55 0 .9 .55;.2 .6 .4 1;.3 0 .3 1" '
            'dur="1.25s" begin="0s" fill="freeze"/>')
    swing_vals = [0, 5.2, -4.3, 3.2, -2.3, 1.5, -.9, .4, 0]
    kt = [i / (len(swing_vals) - 1) for i in range(len(swing_vals))]
    swing = (f'<animateTransform attributeName="transform" type="rotate" calcMode="spline" '
             f'values="{";".join(f"{v} {PIVOT[0]} {PIVOT[1]}" for v in swing_vals)}" '
             f'keyTimes="{";".join(f"{k:.4f}" for k in kt)}" '
             f'keySplines="{";".join([".37 0 .63 1"] * (len(swing_vals) - 1))}" dur="7.5s" begin="0.85s" fill="freeze"/>')
    sway_vals = [0, 1.1, 0, -1.1, 0]
    sway = (f'<animateTransform attributeName="transform" type="rotate" calcMode="spline" '
            f'values="{";".join(f"{v} {PIVOT[0]} {PIVOT[1]}" for v in sway_vals)}" keyTimes="0;.25;.5;.75;1" '
            f'keySplines="{";".join([".37 0 .63 1"] * 4)}" dur="9s" begin="8.3s" repeatCount="indefinite"/>')

    defs = f'''<linearGradient id="strap" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="190"><stop offset="0" stop-color="#cbb8ff"/><stop offset=".6" stop-color="#f4a9c9"/><stop offset="1" stop-color="#f0c98a"/></linearGradient>
<linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff6d6"/><stop offset=".5" stop-color="#d9b96a"/><stop offset="1" stop-color="#a98835"/></linearGradient>
<linearGradient id="card" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{P['card0']}"/><stop offset="1" stop-color="{P['card1']}"/></linearGradient>
<linearGradient id="band" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#cbb8ff"/><stop offset=".55" stop-color="#f8b6d2"/><stop offset="1" stop-color="#fff0b8"/></linearGradient>
<linearGradient id="ring" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8f74d8"/><stop offset=".5" stop-color="#e58ab3"/><stop offset="1" stop-color="#d9b96a"/></linearGradient>
<linearGradient id="nameG" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{P['name0']}"/><stop offset="1" stop-color="{P['name1']}"/></linearGradient>
<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="cardClip"><rect x="{card_x}" y="{y0}" width="{card_w}" height="{card_h}" rx="24"/></clipPath>
<clipPath id="photoClip"><rect x="{photo_x}" y="{photo_y}" width="{photo_w}" height="{photo_h}" rx="16"/></clipPath>
<filter id="blur" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="14"/></filter>
'''
    body = f'''<g>{drop}
<g>{swing}
<g>{sway}
  <g stroke-linecap="butt" fill="none">
    <path d="M118 -30 L{cx} 176" stroke="url(#strap)" stroke-width="26"/>
    <path d="M322 -30 L{cx} 176" stroke="url(#strap)" stroke-width="26" opacity=".94"/>
    <path d="M118 -30 L{cx} 176" stroke="#ffffff" stroke-opacity=".55" stroke-width="1.2" stroke-dasharray="5 5" transform="translate(-6 0)"/>
    <path d="M322 -30 L{cx} 176" stroke="#ffffff" stroke-opacity=".55" stroke-width="1.2" stroke-dasharray="5 5" transform="translate(6 0)"/>
  </g>
  <rect x="{cx-22}" y="158" width="44" height="32" rx="10" fill="url(#metal)" stroke="#9c7d2e" stroke-opacity=".5"/>
  <rect x="{cx-13}" y="166" width="26" height="6" rx="3" fill="#7c6120" opacity=".35"/>
  <path d="M{cx} 190V{y0+20}" stroke="url(#metal)" stroke-width="6" stroke-linecap="round"/>
  <rect x="{card_x+6}" y="{y0+22}" width="{card_w}" height="{card_h}" rx="24" fill="{P['glow']}" opacity="{P['glow_op']}" filter="url(#blur)"/>
  <rect x="{card_x}" y="{y0}" width="{card_w}" height="{card_h}" rx="24" fill="url(#card)" stroke="{P['edge']}" stroke-width="1.5"/>
  <g clip-path="url(#cardClip)">
    <rect x="{card_x}" y="{y0}" width="{card_w}" height="62" fill="url(#band)"/>
    <rect x="{card_x}" y="{y0+62}" width="{card_w}" height="1.5" fill="#ffffff" opacity=".7"/>
    <rect x="{card_x-140}" y="{y0}" width="90" height="{card_h}" fill="url(#shine)" transform="skewX(-16)" opacity="0">
      <animate attributeName="x" values="{card_x-140};{card_x+card_w+140}" dur="2.4s" begin="9s;21s" repeatCount="1" fill="freeze"/>
      <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.9;1" dur="2.4s" begin="9s;21s"/>
    </rect>
  </g>
  <rect x="{cx-32}" y="{y0+15}" width="64" height="11" rx="5.5" fill="{P['notch']}" opacity=".55"/>
  <text x="{cx}" y="{y0+50}" text-anchor="middle" font-family="{MONO}" font-size="11.5" fill="#3a2a66" opacity=".85">data · python · agentic AI</text>
  <rect x="{photo_x-4}" y="{photo_y-4}" width="{photo_w+8}" height="{photo_h+8}" rx="19" fill="url(#ring)"/>
  <image x="{photo_x}" y="{photo_y}" width="{photo_w}" height="{photo_h}" preserveAspectRatio="xMidYMid slice" clip-path="url(#photoClip)" xlink:href="data:image/png;base64,{photo_b64}"/>
  <text x="{cx}" y="{name_y}" text-anchor="middle" font-family="{SERIF}" font-size="28" font-weight="700" fill="url(#nameG)">{esc(NAME)}</text>
  <text x="{cx}" y="{role1_y}" text-anchor="middle" font-family="{SANS}" font-size="13.5" fill="{P['role1']}">Data Analyst · Python Developer</text>
  <text x="{cx}" y="{role2_y}" text-anchor="middle" font-family="{SANS}" font-size="13.5" font-weight="600" fill="{P['role2']}">Agentic AI Developer</text>
  <rect x="{cx-100}" y="{pill_y}" width="200" height="28" rx="14" fill="{P['pill_f']}" stroke="{P['pill_s']}"/>
  <text x="{cx}" y="{pill_y+19}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{P['pill_t']}">@{esc(USER)}</text>
  <line x1="{card_x+22}" y1="{div_y}" x2="{card_x+card_w-22}" y2="{div_y}" stroke="{P['div']}" stroke-dasharray="4 5" stroke-linecap="round"/>
  <path d="{bars}" fill="{P['bars']}"/>
  <text x="{card_x+24}" y="{band_y+90}" font-family="{MONO}" font-size="10.5" fill="{P['scan']}">scan for my GitHub →</text>
  <rect x="{card_x+card_w-qr_size-18}" y="{band_y}" width="{qr_size}" height="{qr_size}" rx="8" fill="#ffffff" stroke="{P['qr_edge']}"/>
  <path d="{path}" fill="#1f1538"/>
</g></g></g>'''
    return defs, body, mods


def build_lanyard(photo_b64, mode="light"):
    """Stand-alone badge SVG (the README normally uses the combined intro scene instead)."""
    defs, body, mods = lanyard_parts(photo_b64, mode)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {VW} {VH}" '
           f'width="{VW}" height="{VH}" role="img" aria-label="{esc(NAME)} — ID badge"><defs>{defs}</defs>{body}</svg>')
    return svg, mods

