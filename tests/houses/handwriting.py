"""Draw a test house's site notes as a phone photo of a handwritten notepad page.

Used by make_houses.py for houses whose notes arrive as photos. The words come from houses.json, so
the answer key always matches what is on the page. Each page is a list of lines; a line can carry
marks: text between [[ and ]] is written, then crossed out. A page can carry "glare"
({"line": n, "over": "19"}) to wash out one word, and "turn" (degrees) for a photo taken sideways.
Same seed, same picture, every run.
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = [Path("C:/Windows/Fonts/Inkfree.ttf"), Path("C:/Windows/Fonts/segoepr.ttf")]
PAGE = (1240, 1640)
MARGIN_X, TOP, LINE_GAP = 120, 170, 92
PAPER, RULE, MARGIN_RULE = (246, 241, 222), (150, 180, 215), (220, 120, 120)
INK = (28, 36, 92)


def font(size):
    for path in FONTS:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise SystemExit("No handwriting font found. Expected Ink Free or Segoe Print in C:/Windows/Fonts.")


def ruled_page():
    page = Image.new("RGB", PAGE, PAPER)
    draw = ImageDraw.Draw(page)
    for y in range(TOP + 30, PAGE[1], LINE_GAP):
        draw.line([(0, y), (PAGE[0], y)], fill=RULE, width=2)
    draw.line([(MARGIN_X - 30, 0), (MARGIN_X - 30, PAGE[1])], fill=MARGIN_RULE, width=3)
    return page


def write_word(page, xy, text, size, rng):
    """One word, letter by letter, each nudged a little off the line like a quick hand."""
    x, y = xy
    for ch in text:
        glyph_font = font(size + rng.randint(-3, 3))
        tile = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((size // 2, size // 3), ch, font=glyph_font, fill=INK + (255,))
        tile = tile.rotate(rng.uniform(-7, 7), resample=Image.BICUBIC)
        page.paste(tile, (int(x) - size // 2, int(y + rng.uniform(-4, 4)) - size // 3), tile)
        x += glyph_font.getlength(ch) * rng.uniform(0.92, 1.05)
    return x


def write_line(page, y, line, size, rng):
    """A line of notes. Text inside [[ ]] is written, then crossed out."""
    draw = ImageDraw.Draw(page)
    x = MARGIN_X + rng.randint(-6, 10)
    for part_index, part in enumerate(line.replace("]]", "[[").split("[[")):
        if not part:
            continue
        start = x
        x = write_word(page, (x, y), part, size, rng)
        if part_index % 2 == 1:
            mid = y + size * 0.55
            draw.line([(start - 4, mid + 6), (x + 2, mid - 8)], fill=INK, width=5)
            draw.line([(start - 2, mid - 6), (x + 4, mid + 4)], fill=INK, width=4)
    return x


def add_glare(page, page_spec):
    """A bright patch over one word, like a flash on glossy paper. glare = {"line": n, "over": "19"}."""
    line = page_spec["lines"][page_spec["glare"]["line"]]
    over = page_spec["glare"]["over"]
    size = page_spec.get("size", 58)
    left = MARGIN_X + font(size).getlength(line[:line.index(over)])
    width = font(size).getlength(over)
    y = TOP + page_spec["glare"]["line"] * LINE_GAP
    glare = Image.new("L", PAGE, 0)
    ImageDraw.Draw(glare).ellipse([left - 10, y - size * 0.55, left + width * 0.85, y + size * 0.6], fill=255)
    glare = glare.filter(ImageFilter.GaussianBlur(12))
    white = Image.new("RGB", PAGE, (255, 255, 250))
    return Image.composite(white, page, glare.point(lambda v: int(v * 0.9)))


def soft_shade(size, angle):
    """A smooth light-to-dark wash across the frame, cut from a larger turned gradient so no edge shows."""
    side = int(max(size) * 1.6)
    wash = Image.linear_gradient("L").resize((side, side)).rotate(angle, resample=Image.BICUBIC)
    left, top = (side - size[0]) // 2, (side - size[1]) // 2
    return wash.crop((left, top, left + size[0], top + size[1]))


def as_photo(page, turn, rng):
    """Tilt, shade one corner, soften, and set it on a table, the way a phone shot comes out."""
    page = page.rotate(rng.uniform(-3.5, 3.5) + turn, resample=Image.BICUBIC, expand=True, fillcolor=(92, 74, 58))
    shade = soft_shade(page.size, rng.choice([35, 145, 215]))
    dark = Image.new("RGB", page.size, (40, 34, 30))
    page = Image.composite(dark, page, shade.point(lambda v: int(v * 0.32)))
    return page.filter(ImageFilter.GaussianBlur(1.1))


def draw_page(page_spec, seed, out_path):
    rng = random.Random(seed)
    page = ruled_page()
    size = page_spec.get("size", 58)
    for index, line in enumerate(page_spec["lines"]):
        if line:
            write_line(page, TOP + index * LINE_GAP - size // 2, line, size, rng)
    if "glare" in page_spec:
        page = add_glare(page, page_spec)
    photo = as_photo(page, page_spec.get("turn", 0), rng)
    photo.convert("RGB").save(out_path, "JPEG", quality=72)
    return out_path


def plain_text(page_spec):
    """What the page says, struck-out text dropped. Used to check the answer key against the page."""
    text = "\n".join(page_spec["lines"])
    while "[[" in text:
        start = text.index("[[")
        text = text[:start] + text[text.index("]]", start) + 2:]
    return text
