# 章节标记样式

按章节在正文中的实际顺序标记。字母模式从 A 开始，超过 Z 继续用 AA、AB、AC……；数字模式从 1 开始，依次用 2、3、4……。图注、正文列表和文章标题沿用原稿自己的编号。

| 模式 | 用途 | 文件 |
| --- | --- | --- |
| `initialis` | 居中彩饰字母，每节随机抽一款 | [样式与上传说明](chapter-markers/initialis.md) |
| `numbers` | 居中彩饰数字，每节随机抽不同的边框与花纹 | [数字素材池与抽取说明](chapter-markers/numbers.md) |

正式排版每篇从 [INITIĀLIS 原站画廊 #54852375](https://initialis.azlen.me/#54852375) 抽款。样式预览里的四枚标记只用于比较字母与数字模式。原站格子每轮随机抽取，同轮每个格子只用一次，换轮时避开相邻重复。抽完保存每节的格子坐标、样式参数和编号，HTML、上传和复查共用这次结果。

**模式与编号不能混淆**：选择「02 动态数字」只是选择数字模式；正文中的 1、2、3……只是章节顺序，不能据此取固定的第1、第2、第3套素材。执行顺序固定为「访问原站并随机抽取不同款式 → 保留各款真实参数 → 将字形重绘为本篇连续编号 → 检查实际 GIF → 上传」。不得拿预览样品或本机固定数字池冒充本篇原站随机抽款。

## 正式稿验收

- 本篇抽取记录必须包含原站地址、各章格子坐标、原始样式参数和最终编号；同篇预览、上传、返修沿用该记录。抽取成功不等于成品已通过。
- 逐枚查看 GIF 的**完全展开帧**及完整循环，再以正文实际的 **42px × 42px** 尺寸检查数字和装饰。展开帧优先按 GIF 中完整图案的长停留帧定位；首帧、末帧可能是收起态，不能只看它们就判定花纹、边框或数字正确。
- 在白底和本篇实际文章背景上确认：数字可辨认，源款花纹/边框仍清楚，装饰没有因更换字形而挤掉、截断或退化成难辨认的普通数字。某枚不合格时，只从本篇尚未使用的原站格子重抽该枚并更新记录，不照搬固定预设补位。
- 上传后检查公众号实际使用的托管图片与动效，确认展开效果、连续编号、42px 显示和循环保留；不能只核对本地 GIF 或上传成功。手机端没有实际查看时，如实说明未验证，不宣称通过。

在浏览器打开可访问 Skill 目录的本地静态页，导入 `assets/chapter-markers/gallery.mjs`。先抽取并保存 JSON，再生成每节的 GIF。字母模式用原站渲染器，数字模式将同一原站参数交给补入数字字形的 [本地引擎](chapter-markers/numbers.md#重渲染和两位以上数字)。

```js
const { drawGalleryChapters, createGalleryMarkerRenderer } =
  await import("/<Skill目录>/assets/chapter-markers/gallery.mjs");
const selection = await drawGalleryChapters("initialis", 4);
const render = await createGalleryMarkerRenderer(selection.mode);
const images = await render(selection.chapters[0]);
```

数字模式调用 `createGalleryMarkerRenderer("numbers", numericEngineUrl)`，引擎地址末尾加斜线。每次 `render(chapter)` 返回按顺序排列的 GIF Blob 数组。保存为任务内素材并目检 42px 下的清晰度。遇到原站访问失败时告知用户，再按用户选择使用离线素材或等原站恢复。

新增模式时，素材独立放在 `assets/chapter-markers/<模式名>/`，规则独立写在 `references/chapter-markers/<模式名>.md`，再加到表中。

新增模式或更新某模式下的款式时，同步刷新章节标题 HTML 动效预览。见 [动效预览生成方式](style-picker.md)。
