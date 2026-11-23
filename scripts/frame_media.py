"""Frame screenshots and recorded GIFs with the built-in screenshot backgrounds, and inspect GIFs.

Usage:
  python -X utf8 scripts/frame_media.py frame 录屏.gif -o 录屏-framed.gif --background 01
  python -X utf8 scripts/frame_media.py frame 截图.png -o 截图-framed.png --background 01
  python -X utf8 scripts/frame_media.py inspect 录屏-framed.gif

Geometry follows the Dinamo screenshot export: margin = 8% of the shorter side,
inner radius = 3% of the shorter side, soft shadow, rounded outer frame.
Static PNG output keeps a transparent outer corner. GIF only has 1-bit
transparency, so GIF corners are composited on white (the WeChat article page).
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageSequence

PICKER = Path(__file__).resolve().parents[1] / "assets" / "style-picker"
BACKGROUND_DIR = PICKER / "backgrounds"
DEFAULT_BACKGROUND = "01"
STATIC_TYPES = {".png", ".jpg", ".jpeg", ".webp"}
# 建议阈值：公众号单张图片按 10 MB 以内准备；本脚本 8 MB 以内算通过，超出给出告警。
GIF_SIZE_WARN_BYTES = 8 * 1024 * 1024
GIF_MIN_WIDTH = 640


# ---------------------------------------------------------------- backgrounds
def load_catalog():
    return json.loads((PICKER / "catalog.json").read_text(encoding="utf-8"))["backgrounds"]


def _hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _soft_light(backdrop, source):
    # W3C compositing spec, values in 0..1.
    low = backdrop - (1 - 2 * source) * backdrop * (1 - backdrop)
    d = np.where(backdrop <= 0.25, ((16 * backdrop - 12) * backdrop + 4) * backdrop, np.sqrt(backdrop))
    high = backdrop + (2 * source - 1) * (d - backdrop)
    return np.where(source <= 0.5, low, high)


def paint_aura(recipe, width, height):
    """Python port of paintScreenshotBackground() for the Aura gradient presets."""
    canvas = np.zeros((height, width, 3), dtype=np.float32)
    canvas[:] = np.array(_hex_rgb(recipe["base"]), dtype=np.float32) / 255
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    for layer in recipe["layers"]:
        cx, cy = width * layer["x"] / 100, height * layer["y"] / 100
        radius = max(width, height) * layer["size"] / 100
        dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / radius
        stops = np.array([0, .42, .78, 1], dtype=np.float32)
        strengths = np.array([1, .72, .22, 0], dtype=np.float32)
        alpha = np.interp(np.clip(dist, 0, 1), stops, strengths) * (layer["opacity"] / 100)
        softness = min(width, height) * layer["blur"] * .0016
        if softness > .5:
            image = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(softness))
            alpha = np.asarray(image, dtype=np.float32) / 255
        color = np.array(_hex_rgb(layer["color"]), dtype=np.float32) / 255
        alpha = alpha[..., None]
        if layer["blend"] == "soft-light":
            mixed = _soft_light(canvas, np.broadcast_to(color, canvas.shape))
            canvas = canvas * (1 - alpha) + mixed * alpha
        else:
            canvas = canvas * (1 - alpha) + color * alpha
    if recipe.get("grain"):
        tile = np.zeros((96, 96), dtype=np.uint8)
        seed = 1297
        for i in range(96 * 96):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            tile[i // 96, i % 96] = 255 if seed >> 31 else 0
        step = max(1, round(width / 400))
        tiled = np.tile(tile, (height // (96 * step) + 1, width // (96 * step) + 1))
        tiled = np.kron(tiled, np.ones((step, step), dtype=np.uint8))[:height, :width].astype(np.float32) / 255
        grain_alpha = (8 + recipe["grain"] * .62) / 255
        mixed = _soft_light(canvas, np.repeat(tiled[..., None], 3, axis=2))
        canvas = canvas * (1 - grain_alpha) + mixed * grain_alpha
    return Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8)).convert("RGBA")


def paint_background(background_id, width, height):
    options = {option["id"]: option for option in load_catalog()}
    if background_id not in options:
        raise ValueError(f"未知背景编号 {background_id}，可用：{', '.join(options)}")
    option = options[background_id]
    if "aura" in option:
        recipes = json.loads((BACKGROUND_DIR / "aura-presets.json").read_text(encoding="utf-8"))
        return paint_aura(recipes[option["aura"]], width, height)
    art = Image.open(BACKGROUND_DIR / option["artwork"]).convert("RGBA")
    scale = max(width / art.width, height / art.height)
    art = art.resize((max(width, round(art.width * scale)), max(height, round(art.height * scale))), Image.LANCZOS)
    left, top = (art.width - width) // 2, (art.height - height) // 2
    return art.crop((left, top, left + width, top + height))


# --------------------------------------------------------------------- framing
def _geometry(w, h, max_width):
    border = min(w, h) * .08
    scale = min(max_width / (w + 2 * border), 4096 / (h + 2 * border), 1.0)  # never upscale
    width, height = round((w + 2 * border) * scale), round((h + 2 * border) * scale)
    inset = border * scale
    inner_w, inner_h = round(w * scale), round(h * scale)
    radius = min(w, h) * scale * .03
    outer = min(32, radius + inset / 3)
    return width, height, round(inset), inner_w, inner_h, radius, outer


def _rounded_mask(size, box, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    return mask


def build_frame(background_id, w, h, max_width):
    """Return (frame RGBA with shadow and card cut-out info, geometry)."""
    width, height, inset, inner_w, inner_h, radius, outer = _geometry(w, h, max_width)
    base = paint_background(background_id, width, height)
    card_box = (inset, inset, inset + inner_w - 1, inset + inner_h - 1)
    card_mask = _rounded_mask((width, height), card_box, radius)
    if background_id == "01":
        shadow_color, blur, offset_y = (255, 184, 107, 170), inset * 1.2, 0
    else:
        shadow_color, blur, offset_y = (5, 20, 24, 82), inset * .85, inset * .2
    shadow = Image.new("RGBA", (width, height), shadow_color[:3] + (0,))
    shadow.putalpha(card_mask.point(lambda v: v * shadow_color[3] // 255))
    shadow = ImageChops.offset(shadow, 0, round(offset_y)).filter(ImageFilter.GaussianBlur(max(0.1, blur / 2)))
    base.alpha_composite(shadow)
    outer_mask = _rounded_mask((width, height), (0, 0, width - 1, height - 1), outer)
    return base, card_mask, outer_mask, (width, height, inset, inner_w, inner_h)


def _compose(frame, card_mask, outer_mask, source, geometry, on_white):
    width, height, inset, inner_w, inner_h = geometry
    canvas = frame.copy()
    inner = source.convert("RGBA").resize((inner_w, inner_h), Image.LANCZOS)
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    layer.paste(inner, (inset, inset))
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), card_mask))
    canvas.alpha_composite(layer)
    canvas.putalpha(outer_mask)
    if on_white:
        white = Image.new("RGBA", canvas.size, (255, 255, 255, 255))
        white.alpha_composite(canvas)
        return white.convert("RGB")
    return canvas


def frame_static(source_path, output_path, background_id=DEFAULT_BACKGROUND, max_width=1200):
    source = Image.open(source_path)
    frame, card_mask, outer_mask, geometry = build_frame(background_id, source.width, source.height, max_width)
    _compose(frame, card_mask, outer_mask, source, geometry, False).save(output_path, "PNG")
    return {"output": str(output_path), "size": list(geometry[:2])}


def frame_gif(source_path, output_path, background_id=DEFAULT_BACKGROUND, max_width=900):
    source = Image.open(source_path)
    info = inspect_gif(source_path)
    if info["errors"]:
        raise ValueError("；".join(info["errors"]))
    frames, durations = [], []
    for raw in ImageSequence.Iterator(source):
        frames.append(raw.convert("RGBA"))
        durations.append(raw.info.get("duration", 100))
    frame, card_mask, outer_mask, geometry = build_frame(background_id, frames[0].width, frames[0].height, max_width)
    composed = [_compose(frame, card_mask, outer_mask, f, geometry, True) for f in frames]
    # One shared palette (background + sampled frames) keeps the background from flickering between frames.
    sample_ids = sorted({round(i * (len(composed) - 1) / max(1, min(len(composed), 8) - 1)) for i in range(min(len(composed), 8))})
    sheet = Image.new("RGB", (composed[0].width, composed[0].height * len(sample_ids)))
    for slot, index in enumerate(sample_ids):
        sheet.paste(composed[index], (0, slot * composed[0].height))
    palette = sheet.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    quantized = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in composed]
    quantized[0].save(output_path, save_all=True, append_images=quantized[1:], duration=durations,
                      loop=0, optimize=False, disposal=1)
    return inspect_gif(output_path)


# ------------------------------------------------------------------ inspection
def inspect_gif(path):
    path = Path(path)
    result = {"path": str(path), "errors": [], "warnings": []}
    if not path.is_file() or path.stat().st_size == 0:
        result["errors"].append(f"实录 GIF 不存在或为空：{path}")
        return result
    image = Image.open(path)
    if image.format != "GIF":
        result["errors"].append(f"不是 GIF 文件：{path}")
        return result
    hashes, total = set(), 0
    count = getattr(image, "n_frames", 1)
    for frame in ImageSequence.Iterator(image):
        hashes.add(hashlib.md5(frame.convert("RGB").tobytes()).hexdigest())
        total += frame.info.get("duration", 0)
    image.seek(0)
    loop = image.info.get("loop")
    size = path.stat().st_size
    result.update({"frames": count, "distinct_frames": len(hashes), "duration_ms": total,
                   "loop": "infinite" if loop == 0 else ("missing" if loop is None else loop),
                   "width": image.width, "height": image.height, "bytes": size,
                   "megabytes": round(size / 1048576, 2)})
    if count < 2 or len(hashes) < 2:
        result["errors"].append("实录 GIF 必须是至少 2 帧、且画面确有变化的真实动画，单帧图或重复帧不能当作实录")
    if loop != 0:
        result["errors"].append("GIF 未设置无限循环（loop=0），请用 frame_media.py frame 重新导出")
    if size > GIF_SIZE_WARN_BYTES:
        result["warnings"].append(f"文件 {result['megabytes']} MB，超过 8 MB 建议值，上传公众号前请压缩或缩短时长")
    if image.width < GIF_MIN_WIDTH:
        result["warnings"].append(f"宽度 {image.width}px 偏小，界面文字可能不清晰，请核对 42px 以下小字")
    result["ok"] = not result["errors"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    framing = sub.add_parser("frame", help="给截图或实录 GIF 加统一背景、留白和圆角")
    framing.add_argument("source", type=Path)
    framing.add_argument("-o", "--output", type=Path, required=True)
    framing.add_argument("--background", default=DEFAULT_BACKGROUND, help="背景编号，沿用本篇所选，默认 01")
    framing.add_argument("--max-width", type=int, help="导出宽度上限，PNG 默认 1200，GIF 默认 900")
    framing.add_argument("--overwrite", action="store_true")
    checking = sub.add_parser("inspect", help="检查实录 GIF 的帧数、循环、尺寸和体积")
    checking.add_argument("source", type=Path)
    args = parser.parse_args()
    if args.command == "inspect":
        report = inspect_gif(args.source)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(0 if report.get("ok") else 1)
    if args.output.exists() and not args.overwrite:
        parser.error(f"目标已存在：{args.output}，如需覆盖请加 --overwrite")
    suffix = args.source.suffix.lower()
    if suffix == ".gif":
        report = frame_gif(args.source, args.output, args.background, args.max_width or 900)
    elif suffix in STATIC_TYPES:
        report = frame_static(args.source, args.output, args.background, args.max_width or 1200)
    else:
        parser.error(f"不支持的格式：{args.source}")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
