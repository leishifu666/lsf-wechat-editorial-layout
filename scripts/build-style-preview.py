"""Build a portable preview with animated samples and screenshot backgrounds."""
import argparse
import base64
import json
from html import escape
from mimetypes import guess_type
from pathlib import Path


ASSETS = Path(__file__).resolve().parents[1] / "assets" / "style-picker"
BACKGROUNDS = ASSETS / "backgrounds"
INTRO_BUNDLE = ASSETS.parent / "intro-wordmark" / "wordmark.bundle.js"
TITLES = {"intro": "开篇动态署名", "chapters": "章节标题样式", "stickers": "文末贴纸", "backgrounds": "截图背景"}
PRESETS = """<section aria-labelledby="preset-label">
<p class="label" id="preset-label">预设</p>
<div id="studio-presets"><form class="preset-tools" id="preset-form">
<input class="preset-name" id="preset-name" type="text" maxlength="32" placeholder="预设名称" aria-label="预设名称">
<button type="submit">保存预设</button>
</form><p class="task-status" id="preset-status" role="status"></p><ul class="preset-list" id="preset-list"></ul></div>
</section>"""


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def image_uri(path):
    mime, _ = guess_type(path.name)
    if mime not in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
        raise ValueError(f"Unsupported image type: {path}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


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


def render_choice(group, option, checked=False):
    label = escape(f'{option["id"]} {option["name"]}')
    option_id = escape(option["id"])
    selected = " checked" if checked else ""
    sample = (
        '<span class="choice-preview choice-empty" aria-hidden="true">留白</span>'
        if group == "stickers" and not option.get("directory")
        else f'<span class="choice-preview" data-option-preview="{group}" aria-hidden="true"></span>'
    )
    return (
        f'<label class="choice"><input type="radio" name="{group}" value="{option_id}"{selected}>'
        f'<span class="choice-card">{sample}<span class="choice-name">{label}</span></span></label>'
    )


def render_group(group, options, choices=None):
    if choices is None:
        choices = [
            render_choice(group, option, checked=index == 0)
            for index, option in enumerate(options)
        ]
    return "\n".join([
        '<fieldset class="style-group">',
        f'<legend>{TITLES[group]}</legend>',
        f'<div class="choices choices-{group}">', *choices, '</div>',
        '</fieldset>',
    ])


def render_sample(group, option, sample, selected):
    path, label = sample
    hidden = "" if selected else " hidden"
    return (
        f'<img class="demo-{group}" data-effect="{group}" data-option="{escape(option["id"])}"'
        f' alt="{escape(label)}" src="{image_uri(path)}"{hidden}>'
    )


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
        '<legend>开篇动态署名</legend>',
        f'<div data-intro-wordmark data-article-workflow="deferred" data-author="{escape(author)}" data-presets="{presets}"'
        f' data-article-lines="{lines}" data-vault="{vault}"></div>',
        '</fieldset>',
    ])


def render_backgrounds(options, screenshot, moonvy):
    bundled_sample = screenshot is None
    screenshot = screenshot or BACKGROUNDS / "github-screenshot.png"
    if bundled_sample:
        moonvy = BACKGROUNDS / "moonvy-sunset.png"

    screenshot_uri = image_uri(screenshot)
    choices = []
    panels = []
    for option in options:
        option_id = escape(option["id"])
        if "artwork" in option:
            artwork = image_uri(BACKGROUNDS / option["artwork"])
            frame = (
                '<div class="screenshot-frame">'
                f'<img class="screenshot-background" src="{artwork}" alt="">'
                f'<img class="screenshot-content" src="{screenshot_uri}" alt="原始页面截图">'
                '</div>'
            )
        elif moonvy:
            frame = f'<img class="screenshot-frame moonvy" src="{image_uri(moonvy)}" alt="Moonvy 日落美化后的截图">'
        else:
            continue

        selected = not choices
        hidden = "" if selected else " hidden"
        choices.append(render_choice("screenshot-background", option, checked=selected))
        panels.append(
            f'<div id="background-{option_id}" data-effect="screenshot-background"'
            f' data-option="{option_id}"{hidden}>{frame}</div>'
        )

    source = (
        '<figcaption class="screenshot-source"><a href="https://github.com/leishifu666/lsf-website-design">'
        'GitHub 仓库截图</a></figcaption>'
        if bundled_sample else ''
    )
    figure = "\n".join([
        '<figure class="background-preview" id="preview-screenshot-background">',
        *panels, source, '</figure>',
    ])
    return render_group("backgrounds", options, choices), figure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("all", "motion", *TITLES), default="all")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--screenshot", type=Path, help="Preview a different real screenshot")
    parser.add_argument("--moonvy", type=Path, help="Moonvy export of the supplied screenshot")
    parser.add_argument("--author", default="雷师傅", help="Default intro wordmark text")
    parser.add_argument("--intro-line", action="append", help="A confirmed opening line to preload (repeat up to 4 times)")
    args = parser.parse_args()
    if args.moonvy and not args.screenshot:
        parser.error("--moonvy requires --screenshot")
    if not args.author.strip():
        parser.error("--author must contain a name")
    article_lines = args.intro_line or []
    if len(article_lines) > 4 or any(not line.strip() for line in article_lines):
        parser.error("Provide 1–4 non-empty --intro-line values")

    catalog = read_json(ASSETS / "catalog.json")
    groups = {
        "all": list(TITLES),
        "motion": ["intro", "chapters", "stickers"],
    }.get(args.group, [args.group])
    template = (ASSETS / "board.html").read_text(encoding="utf-8")
    sections = []
    article = {"INTRO": "", "SCREENSHOT": "", "STICKER": ""}
    article.update({f"CHAPTER {index}": "" for index in range(1, 5)})
    for group in groups:
        if group == "intro":
            sections.append(render_intro(catalog[group], args.author.strip(), article_lines))
            article["INTRO"] = '<div class="intro-stage" id="preview-intro"></div>'
        elif group == "backgrounds":
            controls, article["SCREENSHOT"] = render_backgrounds(catalog[group], args.screenshot, args.moonvy)
            sections.append(controls)
        else:
            sections.append(render_group(group, catalog[group]))
            for index, option in enumerate(catalog[group]):
                if not option.get("directory"):
                    continue
                samples = samples_for(option)
                if group == "chapters":
                    for chapter, sample in enumerate(samples[:4], start=1):
                        article[f"CHAPTER {chapter}"] += render_sample(group, option, sample, index == 0)
                else:
                    sticker = render_sample(group, option, samples[0], index == 0)
                    article["STICKER"] += sticker
    if article["STICKER"]:
        article["STICKER"] = f'<div class="demo-footer" id="preview-stickers">{article["STICKER"]}</div>'
    for name, content in article.items():
        template = template.replace(f"<!-- {name} -->", content)
    bundle = f'<script>{INTRO_BUNDLE.read_text(encoding="utf-8")}</script>' if "intro" in groups else ""
    intro_styles = f'<style>{INTRO_BUNDLE.with_suffix(".css").read_text(encoding="utf-8")}</style>' if "intro" in groups else ""
    additions = {
        "OPTIONS": "\n".join(sections),
        "COPY NAV": '<li><a href="#intro-copy-settings">文案</a></li>' if "intro" in groups else "",
        "PRESET NAV": '<li><a href="#studio-presets">预设</a></li>' if args.group == "all" else "",
        "PRESETS": PRESETS if args.group == "all" else "",
        "PICKER STYLES": f'<style>{(ASSETS / "board.css").read_text(encoding="utf-8")}</style>',
        "PICKER SCRIPT": f'<script>{(ASSETS / "board.js").read_text(encoding="utf-8")}</script>',
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
