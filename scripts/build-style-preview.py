"""Build a portable preview with animated samples and screenshot backgrounds."""
import argparse
import json
from html import escape
from pathlib import Path

from article_preview import (VIDEO_TYPES, article_css, image_uri, layout_styles, load_article,
                             render_article, render_image, video_uri)


ASSETS = Path(__file__).resolve().parents[1] / "assets" / "style-picker"
BACKGROUNDS = ASSETS / "backgrounds"
INTRO_BUNDLE = ASSETS.parent / "intro-wordmark" / "wordmark.bundle.js"
TITLES = {"article-style": "文章风格", "intro": "开篇动态署名", "chapters": "章节标题样式", "backgrounds": "截图背景", "stickers": "文末贴纸"}
HEADINGS = {"article-style": "文章风格", "intro": "开篇署名", "chapters": "章节标题"}


def default_article_styles_catalog():
    script_path = Path(__file__).resolve()
    for parent_index in (1, 3):
        if len(script_path.parents) > parent_index:
            candidate = script_path.parents[parent_index] / "references" / "article-styles" / "catalog.json"
            if candidate.is_file():
                return candidate
    return script_path.parents[1] / "references" / "article-styles" / "catalog.json"
PRESETS = """<section id="studio-presets" class="presets" aria-labelledby="presets-title" tabindex="-1">
<h2 class="group-title" id="presets-title">预设</h2>
<form class="preset-tools" id="preset-form">
<input class="preset-name" id="preset-name" type="text" maxlength="32" placeholder="给当前选择起个名字" aria-label="预设名称" autocomplete="off">
<button type="submit" class="btn-secondary">保存预设</button>
</form><p class="task-status" id="preset-status" role="status"></p><ul class="preset-list" id="preset-list"></ul>
<details class="preset-backup">
<summary>备份预设</summary>
<div><button type="button" class="btn-quiet" id="preset-export">导出</button>
<button type="button" class="btn-quiet" id="preset-import">导入</button>
<input type="file" id="preset-import-file" accept=".json,application/json" hidden></div>
</details>
</section>"""


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def samples_for(option):
    folder = ASSETS / option["directory"]
    if "file" in option:
        return [(folder / option["file"], option["name"])]
    index = read_json(folder / option["index"])
    if "mode" not in option:
        return [(folder / palette["file"], palette["name"]) for palette in index]

    samples = []
    for position, style in enumerate(index):
        glyph = chr(ord("A") + position % 26) if option["mode"] == "initialis" else str(position % 9 + 1)
        samples.append((folder / style / f"{glyph}.gif", glyph))
    return samples


def render_choice(group, option, checked=False, kind="", samples=""):
    label = escape(f'{option["id"]} {option["name"]}')
    option_id = escape(option["id"])
    selected = " checked" if checked else ""
    if group == "stickers" and not option.get("directory"):
        sample = '<span class="choice-preview choice-empty" aria-hidden="true">留白</span>'
    elif samples:
        sample = f'<span class="choice-preview" aria-hidden="true">{samples}</span>'
    else:
        badge = f'<span class="kind-tag">{escape(kind)}</span>' if kind else ""
        sample = f'<span class="choice-preview" data-option-preview="{group}" aria-hidden="true">{badge}</span>'
    return (
        f'<label class="choice"><input type="radio" name="{group}" value="{option_id}"{selected}>'
        f'<span class="choice-card">{sample}<span class="choice-name">{label}</span></span></label>'
    )


def group_heading(group):
    return (
        f'<legend>{TITLES[group]}</legend><div class="group-head">'
        f'<h2 class="group-title">{HEADINGS.get(group, TITLES[group])}</h2>'
        '<span class="picked" data-picked></span></div>'
    )


def render_group(group, options):
    choices = [
        render_choice(group, option, checked=index == 0, samples=(
            "".join(f'<img alt="" src="{image_uri(path)}">' for path, _ in samples_for(option)[:4])
            if group == "chapters" else ""
        ))
        for index, option in enumerate(options)
    ]
    return "\n".join([
        f'<fieldset class="style-group" id="{group}-options">',
        group_heading(group),
        f'<div class="choices choices-{group}">', *choices, '</div>',
        '</fieldset>',
    ])


def render_sample(group, option, sample, selected):
    path, label = sample
    hidden = "" if selected else " hidden"
    source = image_uri(path)
    motion_attributes = ""
    if "poster" in option:
        poster = image_uri(path.with_name(option["poster"]))
        motion_attributes = f' data-still="{poster}" data-animated="{source}"'
        source = poster
    return (
        f'<img class="demo-{group}" data-effect="{group}" data-option="{escape(option["id"])}"'
        f' alt="{escape(label)}" src="{source}"{motion_attributes}{hidden}>'
    )


def chapter_label(index, mode):
    if mode == "numbers":
        return str(index)
    label = ""
    while index:
        index, letter = divmod(index - 1, 26)
        label = chr(ord("A") + letter) + label
    return label


def render_chapter(index, options):
    parts = []
    for option in options:
        folder = ASSETS / option["directory"]
        styles = read_json(folder / option["index"])
        style = folder / styles[(index - 1) % len(styles)]
        label = chapter_label(index, option["mode"])
        glyphs = "".join(f'<img alt="" src="{image_uri(style / (glyph + ".gif"))}">' for glyph in label)
        hidden = "" if option is options[0] else " hidden"
        parts.append(f'<span class="chapter-glyphs" role="img" aria-label="{label}" data-effect="chapters"'
                     f' data-option="{escape(option["id"])}"{hidden}>{glyphs}</span>')
    return "".join(parts)


def render_intro(options, author, article_lines):
    presets = escape(json.dumps(options, ensure_ascii=False))
    vault_assets = ASSETS.parent / "design-how"
    library = read_json(vault_assets / "catalog.json")
    for entry in library:
        if entry["id"] not in {"word-carousel", "roll-type"}:
            entry["thumbnail"] = image_uri(vault_assets / "thumbnails" / f'{entry["id"]}.webp')
    vault = escape(json.dumps(library, ensure_ascii=False))
    lines = escape(json.dumps(article_lines, ensure_ascii=False))
    return "\n".join([
        '<fieldset class="style-group intro-picker">',
        group_heading("intro"),
        f'<div data-intro-wordmark data-article-workflow="deferred" data-author="{escape(author)}" data-presets="{presets}"'
        f' data-article-lines="{lines}" data-vault="{vault}"></div>',
        '</fieldset>',
    ])


def screenshot_tools(index, multiple=False):
    suffix = f"-{index}" if multiple else ""
    label = f"第 {index} 张截图" if multiple else "截图"
    return f"""
<div class="screenshot-tools" data-screenshot-controls>
  <label class="logo-picker">更换截图<input id="screenshot-file{suffix}" data-screenshot-file type="file"
    aria-label="更换{label}" accept="image/png,image/jpeg,image/webp,image/gif"></label>
  <button type="button" id="screenshot-export{suffix}" data-screenshot-export aria-label="导出{label} PNG" disabled>导出 PNG</button>
  <p class="task-status" data-screenshot-status role="status"></p>
</div>"""


def render_backgrounds(options, screenshot_count):
    recipes = read_json(BACKGROUNDS / "aura-presets.json")
    backgrounds = {
        option["id"]: recipes[option["aura"]] if "aura" in option else image_uri(BACKGROUNDS / option["artwork"])
        for option in options
    }
    sources = {option["id"]: [option["name"], option["source"]] for option in options if "source" in option}

    choices = [
        render_choice("screenshot-background", option, checked=option["id"] == options[0]["id"], kind=title)
        for key, title in (("aura", "渐变"), ("artwork", "图片"))
        for option in options if key in option
    ]
    return "\n".join([
        '<fieldset class="style-group" id="screenshot-background-options"'
        f' data-background-sources="{escape(json.dumps(sources))}"'
        f' data-backgrounds="{escape(json.dumps(backgrounds, separators=(",", ":")))}">',
        group_heading("backgrounds"), '<div class="choices choices-backgrounds">', *choices, '</div>',
        screenshot_tools(1) if screenshot_count == 1 else '', '</fieldset>',
    ])


def render_screenshot(block, index, multiple, bundled_sample):
    source = (
        '<a class="screenshot-example-credit" href="https://github.com/leishifu666/lsf-website-design">'
        'GitHub 仓库截图</a>'
        if bundled_sample else ''
    )
    anchor = ' id="preview-screenshot-background"' if index == 1 else ''
    caption = escape(block["caption"])
    is_gif = bool(block.get("is_gif"))
    info = block.get("gif_info") or {}
    meta = (
        f'<p class="gif-meta" data-gif-meta>实录 GIF · {info["frames"]} 帧 · {info["duration_ms"] / 1000:.1f} s · '
        f'{"循环" if info["loop"] == "infinite" else "未循环"} · {info["width"]}×{info["height"]} · {info["megabytes"]} MB'
        + "".join(f' · {escape(w)}' for w in info.get("warnings", [])) + '</p>'
        if is_gif else ''
    )
    # The stage always holds the canvas and the original image. Recorded GIFs keep the <img> visible on top of
    # the canvas so every frame plays inside the same background, padding and corner radius.
    return "\n".join([
        f'<figure class="background-preview{" is-gif" if is_gif else ""}"{anchor}>',
        '<div class="screenshot-stage">',
        f'<canvas class="screenshot-frame" role="img" aria-label="{caption or "加上所选背景的页面截图"}"></canvas>',
        f'<img class="screenshot-original" src="{image_uri(block["screenshot"])}"{"" if is_gif else " hidden"} alt="{caption if is_gif else ""}">',
        '</div>',
        f'<figcaption class="article-caption">{caption}</figcaption>' if caption else '',
        meta,
        '<div class="screenshot-source" hidden>' + source
        + '<a data-background-source target="_blank" rel="noopener" hidden></a></div>',
        screenshot_tools(index, multiple=True) if multiple else '',
        '</figure>',
    ])


def render_video(block, output_dir, opening):
    """Local preview player plus a hidden placeholder that the rich-text copy uses instead of the local file."""
    name = escape(block["video"].name)
    caption = escape(block["caption"])
    poster = f' poster="{image_uri(block["poster"])}"' if block.get("poster") else ""
    kind = "opening" if opening else "inline"
    place = ("请在此处（品牌署名之后、首段正文之前）通过公众号后台「视频」插入已确认成片："
             if opening else "请在此处通过公众号后台「视频」插入本段对应的视频片段：")
    note = ("本地成片预览，能播放不代表公众号原生视频已上传。复制到公众号时，视频不会随富文本带走，"
            "会在品牌署名之后保留插入位置。" if opening else
            "本地片段预览。复制到公众号时会在此处保留视频插入位置。")
    anchor = ' id="preview-opening-video"' if opening else ""
    return "\n".join([
        f'<figure class="demo-video-figure{" opening-video" if opening else ""}"{anchor} data-wechat-video="{kind}"'
        f' data-video-name="{name}">',
        f'<video class="demo-video" controls playsinline preload="metadata"{poster}'
        f' data-src="{video_uri(block["video"], output_dir)}" aria-label="{caption or name}"></video>',
        f'<figcaption class="article-caption">{caption}</figcaption>' if caption else '',
        f'<p class="video-preview-note" data-preview-only>{note}</p>',
        f'<p class="wechat-video-placeholder" data-wechat-video-placeholder="{kind}" hidden>'
        f'【公众号原生视频插入位置：{place}{name}】</p>',
        '</figure>',
    ])


def render_article_styles(options):
    choices = []
    for index, option in enumerate(options):
        option_id = escape(option["id"])
        label = escape(f'{option["id"]} {option["name"]}')
        tagline = escape(option.get("tagline", ""))
        quote = escape(option.get("sample_quote", ""))
        rule_file = escape(option.get("rule_file", ""))
        slug = escape(option.get("slug", ""))
        checked = " checked" if index == 0 else ""
        choices.append(
            f'<label class="choice"><input type="radio" name="article-style" value="{option_id}"'
            f' data-rule="{rule_file}" data-slug="{slug}"{checked}>'
            '<span class="choice-card choice-style-card">'
            f'<span class="choice-name">{label}</span>'
            f'<span class="style-tagline">{tagline}</span>'
            f'<span class="style-quote" aria-hidden="true">“{quote}”</span>'
            '</span></label>'
        )
    return "\n".join([
        '<fieldset class="style-group" id="article-style-options">',
        group_heading("article-style"),
        '<div class="choices choices-article-style">', *choices, '</div>',
        '</fieldset>',
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("all", "motion", *TITLES), default="all")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--article", type=Path, help="UTF-8 article JSON with text and local images")
    parser.add_argument("--screenshot", type=Path, help="Preview a different real screenshot")
    parser.add_argument("--author", default="雷师傅", help="Default intro wordmark text")
    parser.add_argument("--intro-line", action="append", help="A confirmed opening line to preload (repeat up to 4 times)")
    parser.add_argument("--article-styles", type=Path, help="Path to article-styles catalog.json")
    parser.add_argument("--stage", choices=("pre-draft", "final"), default="pre-draft", help="Preview workflow stage")
    parser.add_argument("--video", type=Path, help="The confirmed full video; placed after the wordmark and before the first paragraph")
    parser.add_argument("--video-caption", default="", help="Optional caption under the opening video")
    args = parser.parse_args()
    if not args.author.strip():
        parser.error("--author must contain a name")
    article_lines = args.intro_line or []
    if len(article_lines) > 4 or any(not line.strip() for line in article_lines):
        parser.error("Provide 1–4 non-empty --intro-line values")

    sample = args.article is None
    try:
        article = load_article(args.article or ASSETS / "sample-article.json")
        if args.video:
            if not args.video.is_file() or args.video.suffix.lower() not in VIDEO_TYPES:
                raise ValueError(f"视频必须是存在的 mp4 / webm / mov：{args.video}")
            article["video"] = {"video": args.video, "caption": args.video_caption.strip().rstrip("。."),
                                "poster": article["video"]["poster"] if article["video"] else None}
        blocks = [article["intro"], *(chapter["paragraphs"] for chapter in article["chapters"])]
        screenshots = [block for group in blocks for block in group
                       if isinstance(block, dict) and "screenshot" in block]
        if args.screenshot:
            if not args.screenshot.is_file() or args.screenshot.suffix.lower() not in {".png", ".jpeg", ".jpg", ".webp"}:
                raise ValueError(f"截图必须是存在的 PNG、JPG 或 WebP：{args.screenshot}")
            if screenshots:
                screenshots[0]["screenshot"] = args.screenshot
                screenshots[0]["is_gif"] = False
                screenshots[0].pop("gif_info", None)
            else:
                block = {"screenshot": args.screenshot, "caption": "", "is_gif": False}
                article["intro"].append(block)
                screenshots.append(block)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    catalog = read_json(ASSETS / "catalog.json")
    styles_path = args.article_styles or default_article_styles_catalog()
    article_styles = read_json(styles_path) if styles_path and styles_path.is_file() else []
    groups = {
        "all": list(TITLES),
        "motion": ["intro", "chapters", "stickers"],
    }.get(args.group, [args.group])
    if not article_styles and "article-style" in groups:
        groups.remove("article-style")
    if not screenshots and "backgrounds" in groups:
        groups.remove("backgrounds")
    if not article["chapters"] and "chapters" in groups:
        groups.remove("chapters")
    if not groups:
        parser.error("这篇稿件没有可用于所选预览模式的章节或截图")
    template = (ASSETS / "board.html").read_text(encoding="utf-8")
    sections = []
    intro = ""
    chapter_markers = [""] * len(article["chapters"])
    stickers = []
    for group in groups:
        if group == "article-style":
            sections.append(render_article_styles(article_styles))
        elif group == "intro":
            sections.append(render_intro(catalog[group], args.author.strip(), article_lines))
            intro = '<div class="intro-stage" id="preview-intro"></div>'
        elif group == "backgrounds":
            sections.append(render_backgrounds(catalog[group], len(screenshots)))
        elif group == "chapters":
            sections.append(render_group(group, catalog[group]))
            chapter_markers = [render_chapter(index, catalog[group])
                               for index in range(1, len(article["chapters"]) + 1)]
        else:
            sections.append(render_group(group, catalog[group]))
            for index, option in enumerate(catalog[group]):
                if option.get("directory"):
                    stickers.append(render_sample(group, option, samples_for(option)[0], index == 0))
    footer = f'<footer class="demo-footer" id="preview-stickers">{"".join(stickers)}</footer>' if stickers else ""
    screenshot_indices = iter(range(1, len(screenshots) + 1))

    def screenshot(block):
        if "backgrounds" in groups:
            return render_screenshot(block, next(screenshot_indices), len(screenshots) > 1,
                                     bundled_sample=sample and args.screenshot is None)
        return "" if sample else render_image(block["screenshot"], block["caption"])

    bundle = f'<script>{INTRO_BUNDLE.read_text(encoding="utf-8")}</script>' if "intro" in groups else ""
    intro_styles = f'<style>{INTRO_BUNDLE.with_suffix(".css").read_text(encoding="utf-8")}</style>' if "intro" in groups else ""
    output_dir = args.output.resolve().parent
    opening_video = render_video(article["video"], output_dir, True) if article["video"] else ""
    layout_json = json.dumps(layout_styles(), ensure_ascii=False).replace("</", "<\\/")
    additions = {
        "ARTICLE": render_article(article, intro, chapter_markers, screenshot, footer, sample,
                                  opening_video=opening_video,
                                  video=lambda block: render_video(block, output_dir, False)),
        "DRAFT ATTRIBUTE": "" if sample else " data-draft",
        "OPTIONS": "\n".join(sections),
        "PRESET NAV": (
            '<li class="preset-nav"><button class="preset-toggle" type="button"'
            ' aria-controls="studio-presets" aria-expanded="false">预设</button></li>'
            if args.group == "all" else ""
        ),
        "PRESETS": PRESETS if args.group == "all" else "",
        "PICKER STYLES": (f'<style>{(ASSETS / "board.css").read_text(encoding="utf-8")}\n{article_css()}</style>'
                          f'<script type="application/json" id="article-layout-styles">{layout_json}</script>'),
        "PICKER SCRIPT": "<script>\n" + "\n".join(
            (ASSETS / file).read_text(encoding="utf-8")
            for file in (("screenshot-backgrounds.js", "board.js") if "backgrounds" in groups else ("board.js",))
        ) + "</script>",
        "INTRO SCRIPT": bundle,
        "INTRO STYLES": intro_styles,
    }
    preview = template
    for name, value in additions.items():
        preview = preview.replace(f"<!-- {name} -->", value)
    args.output.write_text(preview, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
