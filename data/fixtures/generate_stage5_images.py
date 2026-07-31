"""Generate the CC0 deterministic product artwork referenced by headphones.json."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "images"
SIZE = 320

COLORS = {
    "黑色": "#252b2b",
    "银色": "#aeb7bb",
    "沙金色": "#b79b76",
    "白色": "#f0f0e8",
    "蓝色": "#4578a8",
    "浅蓝色": "#8cbfd8",
    "深蓝色": "#233f67",
    "灰色": "#777f82",
    "橙色": "#d96c32",
    "米白色": "#d8d0b8",
    "红色": "#b6443d",
    "米色": "#c5ad8b",
    "粉色": "#d78498",
    "绿色": "#4d8969",
    "紫色": "#76528d",
}


def normalized_category(value: str) -> str:
    key = value.casefold().replace("-", "_")
    aliases = {
        "头戴式": "over_ear",
        "over_ear": "over_ear",
        "贴耳式": "on_ear",
        "on_ear": "on_ear",
        "入耳式": "in_ear",
        "in_ear": "in_ear",
        "半入耳式": "semi_in_ear",
        "semi_in_ear": "semi_in_ear",
        "骨传导": "bone_conduction",
        "bone_conduction": "bone_conduction",
        "开放式": "open_ear",
        "open_ear": "open_ear",
    }
    return aliases[key]


def draw_product(record: dict[str, object]) -> Image.Image:
    source_id = str(record["source_id"])
    number = int(source_id.rsplit("-", 1)[1])
    colors = [COLORS.get(str(value), "#56605e") for value in record.get("colors", [])]
    primary = colors[0] if colors else "#252b2b"
    accent = colors[1] if len(colors) > 1 else "#d3f36b"
    background = "#ece9df" if primary != "#f0f0e8" else "#b8c3bf"
    image = Image.new("RGB", (SIZE, SIZE), background)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((20, 20, 300, 300), radius=42, fill="#f8f6ef", outline="#c8cbc4", width=3)
    category = normalized_category(str(record["category"]))

    if category in {"over_ear", "on_ear"}:
        inset = 60 if category == "over_ear" else 76
        width = 20 if category == "over_ear" else 14
        draw.arc((inset, 50, SIZE - inset, 220), 185, 355, fill=primary, width=width)
        cup_width = 54 if category == "over_ear" else 42
        for left in (70, SIZE - 70 - cup_width):
            draw.rounded_rectangle((left, 150, left + cup_width, 246), radius=18, fill=primary)
            draw.rounded_rectangle((left + 9, 164, left + cup_width - 9, 232), radius=12, fill=accent)
    elif category in {"in_ear", "semi_in_ear"}:
        for x, mirror in ((103, -1), (217, 1)):
            radius = 31 if category == "in_ear" else 27
            draw.ellipse((x - radius, 95, x + radius, 95 + radius * 2), fill=primary)
            draw.ellipse((x - 12, 113, x + 12, 137), fill=accent)
            stem_x = x - 8 if mirror < 0 else x
            draw.rounded_rectangle((stem_x, 142, stem_x + 16, 235), radius=8, fill=primary)
            if category == "in_ear":
                tip_x = x + mirror * 34
                draw.ellipse((tip_x - 16, 120, tip_x + 16, 146), fill=accent)
    else:
        y = 163 if category == "bone_conduction" else 145
        draw.arc((58, 78, 262, 252), 10, 170, fill=primary, width=18)
        draw.arc((58, y - 32, 262, y + 106), 190, 350, fill=primary, width=12)
        for x in (74, 218):
            draw.rounded_rectangle((x, y, x + 34, y + 60), radius=14, fill=accent)

    marker_x = 42 + ((number * 37) % 226)
    marker_y = 270 - ((number * 17) % 28)
    draw.ellipse((marker_x, marker_y, marker_x + 12, marker_y + 12), fill=accent)
    return image


def main() -> None:
    payload = json.loads((ROOT / "headphones.json").read_text(encoding="utf-8"))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for record in payload["records"]:
        target = OUTPUT / f"{record['source_id']}.png"
        draw_product(record).save(target, format="PNG", optimize=True)


if __name__ == "__main__":
    main()
