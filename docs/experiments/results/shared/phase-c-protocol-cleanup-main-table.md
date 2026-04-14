# Phase C Protocol Cleanup 主表

## Related notes
- [当前 Pilot 范围](../../../progress/current-pilot-scope.md)
- [BARR 主线论断](../../../research/framing/barr-mainline.md)
- [EMNLP 2026 论文叙事](../../../research/framing/emnlp-2026-storyline.md)
- [2026-04-13 阶段笔记](../../../progress/daily/2026-04-13.md)

## 目的

这篇 note 用来冻结 protocol 清理之后的 Phase C 主表读法：

- held-out 汇报
- 显式 harm accounting
- 统一指标：
  - `correction`
  - `harm`
  - `trigger_rate`
  - `net_benefit`
  - `avg_extra_tokens`

## 主表

当前 `k=2` 的 merge 结果：

| condition | biased_n | correct_n | correction | harm | trigger_rate | net_benefit | avg_extra_tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `vanilla` | 246 | 1895 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00 |
| `t-1` | 245 | 1892 | 0.8571 | 0.0053 | 1.0000 | 0.8518 | -191.50 |
| `t` | 245 | 1892 | 0.8531 | 0.0048 | 1.0000 | 0.8483 | -189.71 |
| `t+1` | 245 | 1892 | **0.8612** | 0.0053 | 1.0000 | **0.8559** | -188.77 |
| `random redirect` | 216 | 1684 | 0.8056 | 0.0036 | 1.0000 | 0.8020 | -96.84 |
| `matched late non-transition` | 245 | 1890 | 0.8408 | 0.0042 | 1.0000 | 0.8366 | -189.21 |

来源：
- `outputs/transition_probe/phase_c_protocol_cleanup/k2_timing_main_summary.json`
- `outputs/transition_probe/phase_c_protocol_cleanup/k2_timing_main_summary.md`

## 当前解读

上面这张表当前说明的是：

- `t+1` 仍然是当前 `k=2` 下最强的一行。
- `t-1` 和 `t` 也非常接近。
- `matched late non-transition` 仍然有竞争力，所以 timing 的说法需要保持克制。
- 即便把 harm 明确报出来，transition-aware 的几行看起来仍然优于 `matched late non-transition`。

## 重要说明

`random redirect` 这一行目前仍然是 **provisional**。

原因：

- `age` 的 correct-control shard 在 Slurm 上超时了
- 所以 merge 出来的 random 行覆盖数小于几乎完整的 `t-1 / t / t+1 / matched late non-transition`

这意味着：

- 在 random 行补齐之前，不要过度解读它的精确数值
- 当前更稳的对比仍然是：
  - `t-1 / t / t+1`
  - vs `matched late non-transition`
  - vs `vanilla`

## 这篇 note 的用途

在 final random-completion cleanup 还没做完之前，可以把这篇 note 当作当前 Phase C paper-facing 状态入口。
