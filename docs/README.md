# BARR 文档说明

这个目录按“用途”组织，不按“创建日期”组织，方便在 VSCode 里直接点着读。

## 先从哪里开始

如果你现在只想最快进入状态，按这个顺序读：

1. [文档导航](index.md)
2. [当前 Pilot 范围](progress/current-pilot-scope.md)
3. [BARR 主线论断](research/framing/barr-mainline.md)
4. [EMNLP 2026 论文叙事](research/framing/emnlp-2026-storyline.md)
5. [2026-04-13 阶段笔记](progress/daily/2026-04-13.md)

## 目录结构

```text
docs/
  README.md
  index.md
  engineering/
    workflows/
  research/
    framing/
    reviews/
  experiments/
    plans/
    results/
  progress/
    current-pilot-scope.md
    daily/
    weekly/
  product/
  archive/
```

## 每个目录放什么

- [`progress/`](progress/README.md)：项目当前状态、daily、weekly、范围冻结。
- [`research/`](research/README.md)：论文主线、thesis framing、review 复盘。
- [`experiments/`](experiments/README.md)：实验计划和结果说明。
- [`engineering/`](engineering/README.md)：协作规则、工作流、维护说明。
- [`product/`](product/README.md)：未来部署或产品化文档的预留区。
- `archive/`：旧版本和 provenance，保留但不作为当前主线入口。

## 命名与链接规则

- 文件名尽量保持稳定，优先用简洁的 `kebab-case`。
- 只有时间型笔记用日期：
  - daily：`YYYY-MM-DD.md`
  - weekly：`YYYY-MM-DD-weekly.md`
- 重要文档顶部都应放一个简短的“相关笔记”区。
- 优先链接到具体笔记，不要只链接到文件夹。
- 旧文档如果被更好的整合文档替代，移动到 `archive/`，不要悄悄删除。

## VSCode 跳转提示

- 在 Markdown 编辑区里，通常需要 `Ctrl + 点击`，macOS 上是 `Cmd + 点击`。
- 在 Markdown Preview 里，一般可以直接点击。
- 这里尽量都用相对路径链接，方便 VSCode 直接跳转。
