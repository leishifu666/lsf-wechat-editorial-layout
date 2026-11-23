"""Load a local article and reuse the publication template's typography in Dinamo."""
import base64
import json
import os
import re
from html import escape
from html.parser import HTMLParser
from mimetypes import guess_type
from pathlib import Path

from frame_media import inspect_gif


ARTICLE_TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "article-template.html"
IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
VIDEO_TYPES = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime"}
VIDEO_INLINE_LIMIT = 25 * 1024 * 1024
BLOCK_KINDS = ("image", "screenshot", "gif", "video")
PLACEHOLDER = re.compile(r"\{\{|\}\}|^\s*(TODO|待补|占位|placeholder)\b", re.I)


class ArticleStyles(HTMLParser):
    def __init__(self):
        super().__init__()
        self.styles = {}

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if "data-layout" in fields:
            self.styles[fields["data-layout"]] = fields["style"]


def layout_styles():
    parser = ArticleStyles()
    parser.feed(ARTICLE_TEMPLATE.read_text(encoding="utf-8"))
    return parser.styles


def article_css():
    styles = layout_styles()
    selectors = {
        "body": ".article-body",
        "paragraph": ".article-body .demo-text",
        "first": ".article-body .demo-text.is-first",
        "heading": ".article-body h2",
        "marker": ".article-body .chapter-heading",
        "glyph": ".article-body .chapter-heading img",
        "emphasis": ".article-body strong",
        "image": ".article-body .demo-image, .article-body .screenshot-frame",
        "caption": ".article-body .article-caption",
        "video": ".article-body .demo-video",
        "video-placeholder": ".article-body .wechat-video-placeholder",
    }
    return "\n".join(f"{selector}{{{styles[role]}}}" for role, selector in selectors.items())


def image_uri(path):
    mime, _ = guess_type(path.name)
    if mime not in IMAGE_TYPES:
        raise ValueError(f"不支持的配图格式：{path}")
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def video_uri(path, output_dir=None):
    """Small videos are inlined as data URIs; large ones fall back to a path relative to the output file."""
    mime = VIDEO_TYPES.get(path.suffix.lower())
    if not mime:
        raise ValueError(f"不支持的视频格式：{path}（支持 mp4 / webm / mov）")
    if path.stat().st_size <= VIDEO_INLINE_LIMIT:
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
    if output_dir is None:
        raise ValueError(f"视频超过 25 MB，需要指定输出目录以便用相对路径引用：{path}")
    return Path(os.path.relpath(path, output_dir)).as_posix()


def validate_gif_file(path):
    report = inspect_gif(path)
    if report["errors"]:
        raise ValueError(f"{path}：" + "；".join(report["errors"]))
    return report


def _resolve(base, value, label, kind):
    if not isinstance(value, str) or not value.strip() or PLACEHOLDER.search(value):
        raise ValueError(f"{label} 缺少真实{kind}素材（路径为空或仍是占位）。请补充后再生成，不能用空占位当作配图已完成")
    source = base / value
    if not source.is_file():
        raise ValueError(f"{label} 找不到本地{kind}素材：{source}")
    return source


def load_article(path):
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict) or not isinstance(raw.get("title"), str) or not raw["title"].strip():
        raise ValueError("稿件 JSON 必须包含非空的 title")

    def video_block(entry, label):
        if isinstance(entry, str):
            entry = {"video": entry}
        if not isinstance(entry, dict) or not isinstance(entry.get("video", entry.get("src")), str):
            raise ValueError(f"{label} 的视频须是路径或包含 video / src 的对象")
        source = _resolve(path.parent, entry.get("video", entry.get("src")), label, "视频")
        if source.suffix.lower() not in VIDEO_TYPES:
            raise ValueError(f"{label} 不支持的视频格式：{source}（支持 mp4 / webm / mov）")
        poster = entry.get("poster")
        if poster:
            poster = _resolve(path.parent, poster, f"{label} 封面", "图片")
        caption = entry.get("caption", "")
        if not isinstance(caption, str):
            raise ValueError(f"{label} 的视频图注须是文字")
        return {"video": source, "caption": caption.strip().rstrip("。."), "poster": poster or None}

    def blocks(values, label):
        if not isinstance(values, list):
            raise ValueError(f"{label} 必须是数组")
        result = []
        for entry in values:
            if isinstance(entry, str) and entry.strip():
                result.append(entry)
                continue
            if not isinstance(entry, dict) or len(set(BLOCK_KINDS) & entry.keys()) != 1:
                raise ValueError(f"{label} 的每项须是正文，或包含 image / screenshot / gif / video 的素材对象")
            kind = next(key for key in BLOCK_KINDS if key in entry)
            if kind == "video":
                result.append(video_block(entry, label))
                continue
            caption = entry.get("caption", "")
            if not isinstance(caption, str):
                raise ValueError(f"{label} 的图片图注须是文字")
            source = _resolve(path.parent, entry[kind], label, "图片" if kind != "gif" else "实录 GIF")
            mime = guess_type(source.name)[0]
            if mime not in IMAGE_TYPES:
                raise ValueError(f"不支持的配图格式：{source}")
            caption = caption.strip().rstrip("。.")
            is_gif = mime == "image/gif"
            if kind == "gif" and not is_gif:
                raise ValueError(f"{label} 的 gif 素材必须是 .gif 文件：{source}")
            if is_gif and kind != "image":
                info = validate_gif_file(source)
                if kind == "gif" and entry.get("framed", True) is False:
                    result.append({"image": source, "caption": caption, "gif_info": info})
                else:
                    result.append({"screenshot": source, "caption": caption, "is_gif": True, "gif_info": info})
                continue
            result.append({kind: source, "caption": caption, "is_gif": False})
        return result

    intro = blocks(raw.get("intro", []), "intro")
    video = video_block(raw["video"], "video") if raw.get("video") else None
    if video is None:
        # An intro video block is the confirmed full video: lift it so it always sits after the wordmark.
        for index, block in enumerate(intro):
            if isinstance(block, dict) and "video" in block:
                video = intro.pop(index)
                break
    chapters = raw.get("chapters", [])
    if not isinstance(chapters, list):
        raise ValueError("chapters 必须是数组")
    sections = []
    for index, chapter in enumerate(chapters, 1):
        if not isinstance(chapter, dict) or not isinstance(chapter.get("title"), str) or not chapter["title"].strip():
            raise ValueError(f"第 {index} 节须包含非空的 title")
        content = blocks(chapter.get("paragraphs"), f"第 {index} 节 paragraphs")
        if not any(isinstance(block, str) for block in content):
            raise ValueError(f"第 {index} 节须有至少一段正文")
        sections.append({"title": chapter["title"].strip(), "paragraphs": content})
    if not sections and not any(isinstance(block, str) for block in intro):
        raise ValueError("稿件须有至少一段正文")
    return {"title": raw["title"].strip(), "video": video, "intro": intro, "chapters": sections}


def paragraph(text, first):
    # Restore only the supported emphasis tag after escaping the whole paragraph.
    text = escape(text).replace("&lt;strong&gt;", "<strong>").replace("&lt;/strong&gt;", "</strong>")
    return f'<p class="demo-text{" is-first" if first else ""}">{text}</p>'


def render_image(path, caption):
    caption = escape(caption)
    return (
        f'<figure><img class="demo-image" src="{image_uri(path)}" alt="{caption}">'
        + (f'<figcaption class="article-caption">{caption}</figcaption>' if caption else "")
        + '</figure>'
    )


def render_article(article, intro, chapter_markers, screenshot, footer, sample, opening_video="", video=None):
    first_paragraph = True

    def render_blocks(blocks):
        nonlocal first_paragraph
        parts = []
        for block in blocks:
            if isinstance(block, str):
                parts.append(paragraph(block, first_paragraph))
                first_paragraph = False
            elif "screenshot" in block:
                parts.append(screenshot(block))
            elif "video" in block:
                if video is None:
                    raise ValueError("稿件含视频片段，但调用方没有提供视频渲染器")
                parts.append(video(block))
            else:
                parts.append(render_image(block["image"], block["caption"]))
        return "\n".join(parts)

    title = escape(article["title"])
    # Opening order is fixed: wordmark/intro motion -> full video -> first paragraph and its figures.
    parts = [f'<header><h1>{title}</h1>',
             f'<p class="sample-meta">{"示例文章" if sample else "本篇稿件"}</p></header>',
             '<div class="article-body">', intro, opening_video, render_blocks(article["intro"])]
    for index, chapter in enumerate(article["chapters"]):
        anchor = ' id="preview-chapters"' if index == 0 else ""
        markers = chapter_markers[index]
        parts.extend([f'<section class="demo-section"{anchor}>',
                      f'<div class="chapter-heading">{markers}</div>' if markers else "",
                      f'<h2>{escape(chapter["title"])}</h2>',
                      render_blocks(chapter["paragraphs"]), '</section>'])
    return "\n".join([*parts, footer, '</div>'])
