---
name: lsf-wechat-editorial-layout
description: 按细字和大留白风格排版微信公众号图文。长文先发 Dinamo HTML 预览，可选开篇动态署名、章节标题、文末贴纸、截图背景和命名预设，再按授权预览或保存草稿
---

# 公众号编辑式排版

将原稿排成可编辑的微信富文本。用户本轮要求优先。只有写作或审稿任务时，直接处理文字。用户授权任选文章试排时，可以用示例文章。

## 先按任务找资料

只读取本轮涉及的专题。选样页使用素材索引和打包脚本直接生成，维护效果时再读对应源码。

| 本轮要做什么 | 入口 |
| --- | --- |
| 发长文选样、修改 Dinamo 界面或管理命名预设 | [选样流程与生成命令](references/style-picker.md) |
| 开篇署名、Agent 文案、Logo 或 GIF 导出 | [开篇署名](references/intro-wordmark.md) · [动效库与分类](references/design-how.md) |
| 章节字母或数字 | [章节标记](references/chapter-markers.md)，再按模式进入字母或数字专题 |
| 文末贴纸与配色 | [文末动效素材库](references/footer-motion-templates.md) |
| 排正文、应用字号和留白 | [正文排版基线](references/article-layout.md) · [文章 HTML 模板](assets/article-template.html) |
| 截图、背景、上传及公众号草稿 | [配图与草稿交付](references/wechat-draft.md) · [Moonvy 参数](references/kuang-screenshots.md) |

素材由两份可执行索引管理。[四组选项](assets/style-picker/catalog.json) 管理选样组与素材位置，[开篇动效索引](assets/design-how/catalog.json) 管理编号和文字、分镜、Logo 三类。新增或调整素材时更新对应索引并重新生成 HTML。既有编号保持稳定。

## 长文工作流

1. 排版前发可直接打开的 Dinamo 动效预览。已明确的选择直接沿用，只补缺项。左侧先选文案来源，再显示对应输入框，然后选动效。右侧在示例正文的实际位置实时预览。
2. 让用户按「复制选择」回传所选编号和可选意见。若选了「Agent 提炼文章」且输入为空，先根据本篇正文给可直接粘贴的短句。用户回填后可手改，以最后确认的内容排版。
3. 章节选定字母或数字后，正式排版每篇从 [INITIĀLIS 画廊](https://initialis.azlen.me/#54852375) 随机抽取。同篇预览、上传和返修共用抽取结果。文末星球按文章配色筛选后抽一款，用户点名配色时直接使用。
4. 截图用实际截图工具。按选定背景加留白和圆角，简短图注末尾不加句号。文章正文和图注保持可编辑。选择保存草稿时按专题步骤检查公众号编辑器和实际预览。
5. 交付时说明已检查的范围。用户确认的长期排版规则写入对应专题，单篇稿件和预设选择留在当前任务。
