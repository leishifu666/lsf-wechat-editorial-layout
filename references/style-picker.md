# 公众号样式动效预览

开工时生成 Dinamo HTML，并发可直接打开的预览链接。桌面左侧选样，右侧在示例文章中实时预览。窄屏用顶部索引跳到文案、预设或文章。开篇区先选「文案来源」，再填写对应输入框，接着选动效。各组默认展示第一款。

选好后点「复制选择」，把编号、款名、文案状态和可选意见粘贴回对话。补充意见默认折叠。完整选样页可命名、套用、改名和删除预设，预设保存在同一浏览器和同一预览来源（协议、主机和端口）内。

| 选项 | 生成参数 | 编号 |
| --- | --- | --- |
| 开篇动态署名 | `--group intro` | 28 款，沿用原编号 |
| 章节标题样式 | `--group chapters` | 01 动态字母，02 动态数字 |
| 文末贴纸 | `--group stickers` | 01 星球变火箭，02 AI 图标旋转环，00 本篇不加 |
| 截图背景 | `--group backgrounds` | 01 日落 · Moonvy，02 星河，03 金雨 |

左栏同时显示署名动效、章节标记、文末贴纸以及截图背景小样，点小样即可选中。字母组和数字组各展示四枚标记，右栏也将它们放入对应章节。正式排版时从 INITIĀLIS 原站抽款。文末贴纸在示例中用代表配色，选定设计后按文章选配色，用户点名配色时直接用指定版本。

开篇署名款式放在一个网格里。左栏保留轻量小样，右栏只启动当前所选的实时渲染。改署名或文章短句后，右栏更新实际文字，复制结果也使用最新文案。各款均可导出当前所选的 640×260 循环 GIF。新增款式时检查编号、小样、实时文案及实际下载文件。

「手写署名」优先载入已保存署名。切到「Agent 提炼文章」时，首次回填框为空，文章开篇显示等待回填。复制选择会附上按正文提炼的任务。拿到短句后粘贴回填，再手改、预览或导出。只有已确认的文案才用 `--intro-line` 显式回填。

## 生成与更新

在 Skill 根目录执行下列命令，将输出路径换成当前任务的交付目录。默认展示全部选项。只需补选一项时加上对应的 `--group`。文章没有截图时加 `--group motion`，只展示动效。

```sh
python -X utf8 scripts/build-style-preview.py --author "雷师傅" --output "公众号样式动效预览.html"
```

生成后用浏览器打开，确认样品与编号对应、动效正常、选项可切换，且「复制选择」复制了当前选项和填写的意见。每次调整素材或索引后重新生成并检查。新增字母或数字款时更新对应目录的 `styles.json`，新增贴纸配色时更新该设计的 `palette-index.json`。署名款用稳定的内部 ID，显示编号沿用已分配的编号，移除款式时保留空号，其他选项沿用索引里的稳定编号。[素材索引](../assets/style-picker/catalog.json)

| 维护层 | 文件 |
| --- | --- |
| 生成入口 | [build-style-preview.py](../scripts/build-style-preview.py) |
| 选样界面 | [布局](../assets/style-picker/board.html) · [样式](../assets/style-picker/board.css) · [选择、复制和预设](../assets/style-picker/board.js) |
| 选项与分类 | [四组选项](../assets/style-picker/catalog.json) · [署名动效](../assets/design-how/catalog.json) |
| 动效实现 | [署名组件](../assets/intro-wordmark/wordmark.jsx) · [效果注册](../assets/intro-wordmark/vault-demos.jsx) |

在同一台电脑的 Codex 桌面端，可把生成的 HTML 作为 `index.html` 放进本任务的独立预览目录，用下列命令提供预览。选择空闲端口，把进程留在后台，打开 Codex 浏览器面板，确认页面加载成功，再发可点击的 HTTP 链接。单独提供 HTML 文件作为离线备份。只服务这个预览目录。

```sh
python -m http.server 8765 --bind 127.0.0.1 --directory "预览目录"
```

预览链接示例为 `http://127.0.0.1:8765/`。若用户在另一台设备，使用该会话提供的可访问预览方式，或交付可直接打开的 HTML 文件附件并说明本机链接的范围。

## 截图背景

左栏样卡只显示底色或背景图，右栏用实际截图预览选中的背景。

默认示例用雷师傅公开的 GitHub 仓库实拍。三款使用同一个原始截图。日落使用 [Moonvy「旷」的导出成品](kuang-screenshots.md)，星河与金雨使用雷师傅提供的两张油画背景，素材放在 `assets/style-picker/backgrounds/`。截图保留原比例，外框与截图均有圆角。油画背景四边留白用日落的尺度，按原截图短边的 8% 换算到成品宽度。这张 GitHub 示例的留边约占成品宽度的 3.17%。

如果已为本篇截好一张样图，可以换成文章截图。先从 Moonvy 导出同一张图的日落款，再传入两个文件生成三款对照。

```sh
python -X utf8 scripts/build-style-preview.py --group backgrounds --screenshot "原始截图.png" --moonvy "Moonvy日落.png" --output "截图背景预览.html"
```

正式配图选择 02 或 03 时，用原图传入 `--screenshot`，省略 `--moonvy`，打开 HTML 并切换到选定的背景。导出时给页面追加 `:root, .article-demo { background: transparent; }`，用浏览器截图工具以透明背景截取可见的 `.screenshot-frame`（如 Playwright 的 `omit_background=True`）。用约 600 CSS px 的卡片宽度、2× 像素比例输出 PNG，检查圆角像素透明、截图文字清楚。图注在文章里单独排。将 PNG 上传微信后，再检查实际图片边缘和文字。
