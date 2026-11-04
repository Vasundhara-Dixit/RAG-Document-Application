import base64, io
from PIL import Image
from pathlib import Path
SRC = Path(__file__).resolve().parent.parent / "assets" / "source" / "portrait.png"

def png_b64(img):
    buf = io.BytesIO(); img.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

def banner_image_b64(w=540):
    im = Image.open(SRC).convert("RGB")
    return png_b64(im.resize((w, int(w * 1.5)), Image.LANCZOS))

def badge_image_b64(w=420):
    im = Image.open(SRC).convert("RGB")
    crop = im.crop((175, 200, 695, 200 + 650))       # 4:5 crop around the face/shoulders
    return png_b64(crop.resize((w, int(w * 1.25)), Image.LANCZOS))
