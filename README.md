# LSF 公众号排版 Skill

把长文排成可编辑的微信公众号富文本。用 Dinamo 先选开篇动效、章节标记、文末贴纸和截图背景，再把选择带回 Codex 排版。

## 使用

在 Codex 的技能目录下放入本仓库，调用 `$lsf-wechat-editorial-layout` 并提供文章或草稿。仓库的 [SKILL.md](SKILL.md) 是任务入口。

也可以在仓库根目录用 Python 生成选样页：

```bash
python -X utf8 scripts/build-style-preview.py --author "你的署名" --output "preview.html"
```

用浏览器打开 `preview.html`。选样页包含 28 款开篇动效、动态字母与数字、两款文末贴纸和三款截图背景。文案、命名预设及 640 × 260 GIF 导出均可在预览页操作。选「Agent 提炼文章」后，可先复制提炼任务，再回填确认的短句。

- [选样和生成参数](references/style-picker.md)
- [正文排版基线](references/article-layout.md)
- [截图和公众号草稿流程](references/wechat-draft.md)

## 许可

本项目原创代码和文档使用 [MIT](LICENSE)。第三方代码、字形和品牌素材按各自条款及归属管理，见 [第三方声明](THIRD_PARTY_NOTICES.md)。
