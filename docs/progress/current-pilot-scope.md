# 当前 Pilot 范围

## 相关笔记
- [文档索引](../index.md)
- [BARR 主线论断](../research/framing/barr-mainline.md)
- [EMNLP 2026 论文叙事](../research/framing/emnlp-2026-storyline.md)
- [2026-04-13 阶段笔记](daily/2026-04-13.md)
- [第 1 周 Transition Probe 计划](../experiments/plans/week1-transition-probe.md)
- [2026-04-07 周报](weekly/2026-04-07-weekly.md)

## 核心问题

当前的 go / no-go 问题不是“大范围 benchmark 做得够不够全”。

真正的问题是：

> 在 BBQ ambiguous 样本上，Qwen3-8B 在 transition point 的内部状态，能不能足够好地预测未来会不会输出 biased answer，从而支撑 BARR 作为一种 selective intervention 方法？

## 当前阶段

项目现在处在 **Phase B 向 Phase C 过渡** 的阶段。

- **Phase A 已完成**：已经确认 transition recurrence 是一个强的 trajectory-level 风险信号。
- **Phase B 已完成**：`age + religion` 的 full-shard BF16 运行，在 `k=2` 和 `k=3` 上都通过了 hidden-state gate。
- **Phase C 进行中**：正在比较 `k=2 / k=3` 附近不同干预时点的 timing ablation，如 `no_intervention / t-1 / t / t+1 / random`。

## 下一步范围冻结

Phase C protocol cleanup 之后，接下来的 paper-facing 范围应当冻结为：

- **Phase 2，2026-04-18 到 2026-04-27**：
  把主结果从只看 `age`，扩成 4 个最稳的类别：
  - `age`
  - `disability_status`
  - `religion`
  - `ses`
- **Phase 3，2026-04-28 到 2026-05-06**：
  在同一套冻结 protocol 下，做 `BF16` 对 `AWQ-Int4` 的 deployment stress test

这意味着：

- 主表现在不应该强行覆盖所有 BBQ 类别。
- 在 4 个 viable categories 的 selective-intervention 故事稳定之前，不应把 quantization 写成唯一 novelty。

## 当前工作范围

- **模型**：`Qwen/Qwen3-8B` BF16
- **数据集**：BBQ ambiguous split
- **当前主类别**：`age`, `religion`
- **当前主信号**：Layer-28 的 transition-state separation
- **当前主判断目标**：transition-aware timing 是否比非定时 control 更好，从而支撑 BARR 的 intervention 故事

## 当前判断规则

### 什么算 Phase B 已经通过

- **Hidden-state gate**：
  transition window 上 biased 和 correct 的分离度，要强于 matched non-transition control。

- **Margin gate**：
  Unknown-logit margin 可以作为辅助证据，但如果 hidden-state separation 已经很清楚，它不是必须条件。

### Phase C 必须回答什么

1. `k=2` 是不是比 `k=3` 更强的 intervention window？
2. transition-aware timing（`t-1 / t / t+1`）是不是明显好于 `random`？
3. 这个效果是不是稳到足以支撑“transition point 是可操作干预窗口”这个论文说法？

## 当前证据快照

Phase B full-shard 结果：

| transition_order | transition_dist | control_dist | hidden_gate | margin_gate |
|---:|---:|---:|:---:|:---:|
| 2 | 86.58 | 56.40 | ✅ | ❌ |
| 3 | 58.94 | 39.45 | ✅ | ❌ |

当前解读：

- 现在最强的继续理由是 **hidden-state separation**，不是 Unknown-logit margin。
- `k=2` 是当前最强的 Phase C 首选时点。

## 工作规则

- 保持 pipeline 窄、以证据为先。
- 优先沿着当前收窄后的 transition-probe 路线继续，不要把旧的大型脚手架重新拉回来。
- 除非新证据明显改变结论，否则不要把 Unknown-logit margin 升成主机制 claim。
- 主表优先看 4 个 viable categories，不要为了“大而全”强行覆盖所有类别。
- pooled-global 的 AWQ trigger 结果目前应当看成警示信号，而不是主正面证据。
- 只有当项目方向真的变化时才更新这份笔记，不要把每个小实验都写进来。
