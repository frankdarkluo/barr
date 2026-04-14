# BARR 文档导航

这是一页专门给日常阅读和 VSCode 跳转用的导航页。

提示：
- 在 VSCode 的 Markdown 编辑区里，通常需要 `Ctrl + 点击` 才会跳转。
- 如果你打开的是 Markdown Preview，一般可以直接点击链接。
- 这页只放“现在最值得点”的入口，不追求把所有文档都塞进来。

## 最短阅读路径

如果你现在只想最快搞清楚“我们在做什么”，按这个顺序读：

1. [当前 Pilot 范围](progress/current-pilot-scope.md)
2. [BARR 主线论断](research/framing/barr-mainline.md)
3. [EMNLP 2026 论文叙事](research/framing/emnlp-2026-storyline.md)
4. [2026-04-13 阶段笔记](progress/daily/2026-04-13.md)
5. [Phase C Protocol Cleanup 主表](experiments/results/shared/phase-c-protocol-cleanup-main-table.md)
6. [Phase 2 四类主表与 Phase 3 部署压力测试](experiments/plans/phase2-viable-categories-and-phase3-deployment-stress-test.md)

## 现在在做什么

- [当前 Pilot 范围](progress/current-pilot-scope.md)
  现在的核心问题、当前阶段、下一步范围冻结。
- [2026-04-13 阶段笔记](progress/daily/2026-04-13.md)
  当前最值得引用的结论、主表范围、protocol freeze。
- [2026-04-08 实验日志](progress/daily/2026-04-08.md)
  当天原始实验过程和结果明细。
- [2026-04-07 周报](progress/weekly/2026-04-07-weekly.md)
  本周 checkpoint 和阶段变化。

## 论文怎么讲

- [BARR 主线论断](research/framing/barr-mainline.md)
  一句话说清主 claim、reviewer-safe protocol、当前最优先的下一步。
- [EMNLP 2026 论文叙事](research/framing/emnlp-2026-storyline.md)
  论文的讲法、哪些地方不要 oversell、目标表格是什么。
- [Stage 1 / Stage 2 复盘交接](research/reviews/stage1-stage2-claude-handoff.md)
  为什么主表应优先放 4 个 viable categories。

## 最该看的结果

- [Phase C Protocol Cleanup 主表](experiments/results/shared/phase-c-protocol-cleanup-main-table.md)
  当前最直接的 Phase C 主表入口。
- [AWQ Age 选择性触发总览](experiments/results/age/awq-age-selective-trigger-overview.md)
  age slice 的主结果整合版。
- [AWQ Age 干预主表](experiments/results/age/awq-age-intervention-main-table.md)
  age slice 的原始 intervention 对比表。
- [AWQ Shared Strict-Online 进展](experiments/results/shared/awq-shared-strict-online-progress.md)
  pooled shared policy 为什么目前不能当强正面结果。

## 接下来要做什么

- [Phase 2 四类主表与 Phase 3 部署压力测试](experiments/plans/phase2-viable-categories-and-phase3-deployment-stress-test.md)
  主表扩到 4 个 viable categories，以及 quantization 作为 stress test 的计划。
- [第 1 周 Transition Probe 计划](experiments/plans/week1-transition-probe.md)
  最早的 mechanistic pilot 执行计划，适合回看设计初衷。
- [第 1 周 Qwen3 Thinking Mode 计划](experiments/plans/week1-qwen3-thinking-mode.md)
  较早期的 thinking-mode 计划背景。

## 如果你想追细节

- [进度 README](progress/README.md)
  `progress/` 目录的用途说明。
- [实验 README](experiments/README.md)
  `experiments/` 目录的用途说明。
- [研究 README](research/README.md)
  `research/` 目录的用途说明。
- [文档 README](README.md)
  整个 `docs/` 目录的结构和命名规则。

## 工程与协作规则

- [工作流效率规则](engineering/workflows/efficiency.md)
- [AI 协作工作流](engineering/workflows/ai-collaboration-workflow.md)
- [研究项目工作流](engineering/workflows/research-project-workflow.md)
- [Daily Research Log Skill](engineering/workflows/daily-research-log-skill.md)

## 暂时不用先看

- `docs/archive/`
  主要是历史版本和 provenance，不是当前主线入口。
- `docs/references/`
  主要是参考论文和 PDF。
- [产品化文档预留区](product/README.md)
  目前还是预留区。
