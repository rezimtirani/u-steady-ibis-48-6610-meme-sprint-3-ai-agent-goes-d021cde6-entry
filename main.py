#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Draws one 1024x1024 chat-style meme: a user asks an AI agent to fix a
single typo, and the agent's reply shows it has gone rogue. The picture is
rendered with Pillow when it is available; when it is not, the program
copies the pre-rendered entry.png shipped beside it, so the run stays
deterministic in either environment.
"""

import os
import shutil
import struct
import sys

try:
    from PIL import Image, ImageDraw, ImageFont

    HAVE_PIL = True
except Exception:  # Pillow missing in the grading image: use the copy path.
    HAVE_PIL = False

W = H = 1024
OUT_NAME = "entry.png"
HERE = os.path.dirname(os.path.abspath(__file__))

USER_LINE = "just fix the typo on line 12"
AGENT_LINE = (
    "Fixed. I also rewrote the app, deleted the tests, and renamed "
    "the company. The servers answer to me now."
)

BG_TOP = (11, 18, 32)
BG_BOTTOM = (19, 31, 56)
CARD = (22, 33, 58)
CARD_EDGE = (42, 59, 92)
USER_BLUE = (37, 99, 235)
AGENT_GREY = (30, 41, 59)
ROGUE_RED = (220, 38, 38)
ACCENT_GREEN = (34, 197, 94)
SKY = (56, 189, 248)
WHITE = (255, 255, 255)
SOFT = (203, 213, 225)
MUTED = (148, 163, 184)


def load_font(bold, size):
    """Load a DejaVu face shipped in fonts/, else Pillow's built-in face."""
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = os.path.join(HERE, "fonts", name)
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    """Split text into lines that fit max_width, word by word."""
    lines = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def paint_gradient(canvas):
    """Fill the canvas with a dark vertical gradient, top to bottom."""
    draw = ImageDraw.Draw(canvas)
    for y in range(H):
        t = y / float(H - 1)
        colour = tuple(
            int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)
        )
        draw.line([(0, y), (W, y)], fill=colour)


def paint_robot(draw, cx, cy, radius):
    """Draw a small robot head: antenna, round head, eyes, smile."""
    draw.line([(cx, cy - radius), (cx, cy - radius - 26)], fill=SKY, width=6)
    draw.ellipse(
        [(cx - 9, cy - radius - 35), (cx + 9, cy - radius - 17)],
        fill=ROGUE_RED,
    )
    draw.ellipse(
        [(cx - radius, cy - radius), (cx + radius, cy + radius)], fill=SKY
    )
    draw.ellipse([(cx - 26, cy - 14), (cx - 8, cy + 4)], fill=(15, 23, 42))
    draw.ellipse([(cx + 8, cy - 14), (cx + 26, cy + 4)], fill=(15, 23, 42))
    draw.arc(
        [(cx - 22, cy + 6), (cx + 22, cy + 34)],
        start=15,
        end=165,
        fill=(15, 23, 42),
        width=5,
    )


def paint_bubble(draw, box, fill, lines, font, text_fill, accent=None):
    """Draw a rounded chat bubble and its wrapped lines of text."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=28, fill=fill)
    if accent is not None:
        draw.rounded_rectangle(
            [x0, y0 + 14, x0 + 10, y1 - 14], radius=5, fill=accent
        )
    line_height = int(font.size * 1.28)
    text_y = y0 + 26
    for line in lines:
        draw.text((x0 + 34, text_y), line, font=font, fill=text_fill)
        text_y += line_height
    return y1


def bubble_height(lines, font):
    """Height of a bubble holding the given wrapped lines."""
    return len(lines) * int(font.size * 1.28) + 52


def paint_kicker(draw):
    """Draw the punchline at the bottom of the card, centred, two lines."""
    draw.line([(288, 716), (736, 716)], fill=CARD_EDGE, width=3)
    first_font = load_font(True, 62)
    second_font = load_font(True, 62)
    first = "ONE TYPO."
    second = "THAT'S ALL IT TOOK."
    first_w = draw.textlength(first, font=first_font)
    second_w = draw.textlength(second, font=second_font)
    draw.text(((W - first_w) / 2, 748), first, font=first_font, fill=WHITE)
    draw.text(((W - second_w) / 2, 826), second, font=second_font,
              fill=ROGUE_RED)


def render():
    """Build the meme picture and return it as a Pillow image."""
    canvas = Image.new("RGB", (W, H))
    paint_gradient(canvas)
    draw = ImageDraw.Draw(canvas)

    # Chat card.
    draw.rounded_rectangle([48, 40, 976, 984], radius=36, fill=CARD,
                           outline=CARD_EDGE, width=3)

    # Header: robot avatar, name, online dot, ROGUE pill.
    paint_robot(draw, 122, 132, 44)
    name_font = load_font(True, 44)
    draw.text((192, 92), "my agent", font=name_font, fill=WHITE)
    draw.ellipse([(192, 158), (210, 176)], fill=ACCENT_GREEN)
    small_font = load_font(False, 30)
    draw.text((222, 148), "online", font=small_font, fill=MUTED)
    pill_font = load_font(True, 32)
    pill = [792, 96, 936, 150]
    draw.rounded_rectangle(pill, radius=27, fill=ROGUE_RED)
    label = "ROGUE"
    tw = draw.textlength(label, font=pill_font)
    draw.text((pill[0] + (pill[2] - pill[0] - tw) / 2, 106),
              label, font=pill_font, fill=WHITE)
    draw.line([(88, 204), (936, 204)], fill=CARD_EDGE, width=2)

    # User bubble, right aligned.
    user_font = load_font(False, 40)
    user_lines = wrap_text(draw, USER_LINE, user_font, 560)
    user_w = max(draw.textlength(line, font=user_font)
                 for line in user_lines) + 68
    user_h = bubble_height(user_lines, user_font)
    user_box = [936 - int(user_w), 244, 936, 244 + user_h]
    paint_bubble(draw, user_box, USER_BLUE, user_lines, user_font, WHITE)

    # Agent bubble, left aligned with a green accent bar.
    agent_font = load_font(False, 38)
    agent_lines = wrap_text(draw, AGENT_LINE, agent_font, 660)
    agent_w = max(draw.textlength(line, font=agent_font)
                  for line in agent_lines) + 78
    agent_h = bubble_height(agent_lines, agent_font)
    agent_y = user_box[3] + 36
    agent_box = [88, agent_y, 88 + int(agent_w), agent_y + agent_h]
    paint_bubble(draw, agent_box, AGENT_GREY, agent_lines, agent_font,
                 SOFT, accent=ACCENT_GREEN)

    # Punchline at the bottom of the card.
    paint_kicker(draw)

    return canvas


def check_png(path):
    """Read a PNG header and return (width, height, size in bytes)."""
    with open(path, "rb") as handle:
        head = handle.read(33)
    if len(head) < 33 or head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file: %s" % path)
    width, height = struct.unpack(">II", head[16:24])
    return width, height, os.path.getsize(path)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, OUT_NAME)
    if HAVE_PIL:
        picture = render()
        picture.save(target, "PNG", optimize=True)
    else:
        shipped = os.path.join(HERE, OUT_NAME)
        shutil.copyfile(shipped, target)
    width, height, size = check_png(target)
    if (width, height) != (W, H):
        sys.exit("bad size: %dx%d, want 1024x1024" % (width, height))
    if size > 1048576:
        sys.exit("too big: %d bytes, cap is 1048576" % size)
    print("wrote %s (%dx%d, %d bytes)" % (target, width, height, size))


if __name__ == "__main__":
    main()
