# 正文排版基线

公众号参考为 [AI设计师阿东的原文](https://mp.weixin.qq.com/s/0ttPQ8sYJRvnRs7Gj6k-6Q)。保留原稿事实与顺序，每节至少有一段完整正文。

| 元素 | 参数 |
| --- | --- |
| 开篇动态署名 | 正文最前 / 约 2.46:1 的横幅 GIF / 占正文栏宽 / 底部留 24px |
| 正文 | 16px / 300 字重 / 1.9 行高 / #1a1a1a / 左对齐 |
| 字体 | -apple-system, BlinkMacSystemFont, Helvetica Neue, PingFang SC, Microsoft YaHei, sans-serif |
| 字间距 | 0.544px，试样显式固定；参考文章为继承微信页面 |
| 段落 | margin:40px 0；首段 0 0 40px；不首行缩进 |
| 外层 | 左右各 6px 内边距，叠加微信原有边距 |
| 章节标题 | 22px / 500 / 行高1.4 / 居中 / 下方56px |
| 强调 | 正文同字号 / 400 字重 / #5e8e3e |
| 图片 | width:100% / height:auto / display:block / 8px圆角 |
| 图注 | 11px / 400 / #aaa / 行高1.4 / 居中 / margin:8px 0 18px / 左右padding:10% |
| 章节标记 | 按本篇选定的模式取用 INITIĀLIS 透明 GIF，42px 居中，66px 高容器，上方 40px |

基线是待用户继续校准的样式，不固定文章章节数。字体与细字重因设备而异。原图注颜色较浅；用户要求加深时直接调整。需要 HTML 起点时用 [assets/article-template.html](../assets/article-template.html)，不要将网页预览工具栏一起复制进正文。
