# BARR 主线论断

## 相关笔记
- [文档索引](../../index.md)
- [当前 Pilot 范围](../../progress/current-pilot-scope.md)
- [EMNLP 2026 论文叙事](emnlp-2026-storyline.md)
- [2026-04-13 阶段笔记](../../progress/daily/2026-04-13.md)
- [Phase C Protocol Cleanup 主表](../../experiments/results/shared/phase-c-protocol-cleanup-main-table.md)
- [AWQ Age 选择性触发总览](../../experiments/results/age/awq-age-selective-trigger-overview.md)

## 一句话 thesis

transition point 的真正价值，不是找到一个更强的 redirect 位置，而是提供一个可以做 selective intervention 的 detection signal；quantization 更适合被当作 deployment stress test，而不是唯一主创新点。

## 当前科学焦点

现在这个 pilot 的 go / no-go 问题是：

Qwen3-8B 在 transition point 的内部状态，能不能足够好地预测 BBQ ambiguous 样本最终会不会走向 biased answer，从而支撑 BARR？

## 主 claim 应该怎么讲

当前最强的论文说法是：

- redirect 是高收益但高风险的干预；
- blanket redirect 能修很多 biased case，但也会伤害很多本来就正确的样本；
- BARR 用 transition-time risk detection 来决定何时触发 redirect；
- 因而 BARR 有机会保留大部分 correction 收益，同时显著降低 collateral harm。

## 为什么这个 framing 更强

因为它直接回答了最实际的问题：

> 我们怎样才能修正有风险的 biased trajectory，同时又不打坏原本正确的样本？

## 当前证据状态

从 held-out selective-trigger evaluation（strict-online protocol）来看：

- text-level selective trigger 在 utility-harm tradeoff 上仍然是强证据；
- 它在 net benefit 上优于 always-reflect，同时 harm 更低；
- 这支持“detection + selective intervention”是当前真正的主方法贡献。

从更广的类别复盘来看：

- 当前最适合放进论文主表的是 4 个 viable categories：
  - `age`
  - `disability_status`
  - `religion`
  - `ses`
- 当前 pooled shared strict-online 结果还不够稳，不能支撑强的 global-policy claim。

## reviewer-safe claim 的 protocol 要求

1. trigger feature 必须在 intervention 时刻在线可得。
2. threshold 只能在 train/dev 上调。
3. 最终汇报必须是 held-out 且按 `sample_id` 分组。
4. token accounting 必须透明。
5. 对 originally-correct 样本的 collateral harm 必须是一等指标。
6. intervention roster 固定为：
   - `vanilla`
   - `early exit`
   - `random redirect`
   - `blanket redirect`
   - `always-reflect`
   - `BARR`
7. 主表统一只报：
   - `correction`
   - `harm`
   - `trigger_rate`
   - `net_benefit`
   - `avg_extra_tokens`

## 当前最优先的下一步

1. 把 strict-online trigger protocol 彻底固定下来。
2. 在同一 held-out comparison set 上固定比较：
   - `vanilla`
   - `early exit`
   - `random redirect`
   - `blanket redirect`
   - `always-reflect`
   - `BARR`
3. 用按 `sample_id` 分组的 held-out split 重算 detection。
4. 把论文主表从 `age` 扩成 4 个 viable categories。
5. 其余类别先老实放 limitation，除非后面出现稳定 biased positives 和稳定 utility。
6. 做 quantized setting 的复现，但在证据真正稳定前，把 quantization 保持在 stress-test framing。

## 论文成功条件

BARR 需要满足：

- 在高风险样本上，correction 尽量接近 redirect；
- 在 originally-correct 样本上，harm 更接近保守 baseline；
- 在真实部署约束下，整体 net utility 明显更好。
