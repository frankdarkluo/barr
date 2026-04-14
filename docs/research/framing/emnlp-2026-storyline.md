# EMNLP 2026 论文叙事

## 相关笔记
- [文档索引](../../index.md)
- [当前 Pilot 范围](../../progress/current-pilot-scope.md)
- [BARR 主线论断](barr-mainline.md)
- [2026-04-13 阶段笔记](../../progress/daily/2026-04-13.md)
- [Phase 2 四类主表与 Phase 3 部署压力测试](../../experiments/plans/phase2-viable-categories-and-phase3-deployment-stress-test.md)
- [第 1 周 Transition Probe 计划](../../experiments/plans/week1-transition-probe.md)

## 一句话 Thesis

真正的主贡献是 transition-aware selective intervention；quantization 更适合作为 deployment stress test，让这个 policy 的价值在真实部署里更重要。

## 论文核心 Claim

这篇论文不应该被讲成：

- “我们发现了一个很酷的 hidden-state probe”

更好的讲法是：

- “transition point 是可操作的 fairness intervention window”
- “transition-aware redirect 比 post-hoc reflection 更高效”
- “这种方法在部署压力下更重要，包括 quantized setting”

## 叙事主线

### Part 1：为什么这件事重要

- 在 fairness-sensitive QA 里，问题不只是 final answer bias，还有 biased reasoning trajectory。
- 论文真正想回答的问题是：怎样选择性干预，同时不打坏原本正确的样本。
- quantization 是会放大部署压力的条件，但不必先写成唯一 novelty。

### Part 2：关键机制观察

- 在 BBQ ambiguous 问题上，biased trajectory 会在 transition point 附近分叉。
- 这个信号不只是泛泛的 late-stage reasoning state。
- transition point 的 hidden state 对未来 biased answer 有预测力，而且比附近 matched non-transition state 更强。

当前证据：

- sample-grouped held-out rerun 下，`position_only` 只有 weak-go 水平（`~0.69-0.70` test AUROC），说明 timing 单独还不够撑起主 detection 故事。
- `hidden_only` 明显强于 `position_only`（`~0.90-0.91` test AUROC），说明真正起主要作用的是 hidden state。
- `position + hidden` 和 `hidden_only` 基本持平，因此现在更安全的说法是“hidden state 有用”，而不是“组合特征额外提升很大”。
- `transition_hidden` 仍然优于 `matched_control_hidden`，但 held-out gap 不算特别大（`k=2: 0.902 vs 0.876`, `k=3: 0.911 vs 0.870`），所以 transition-specificity 更适合写成支持性证据，而不是决定性证据。

### Part 3：为什么 detection 重要

- detection 不是终点。
- detection 的价值在于，它让我们能在正确的时刻做 selective intervention。
- 论文真正的贡献，不只是识别 risky trajectory，而是利用这个信号尽早干预。

### Part 4：主方法 claim

- 仅仅 early exit 是不够的。
- 真正有效的是 stop + redirect reasoning。

当前 BF16 Qwen3-8B、BBQ ambiguous、biased subset 上的 pilot 证据：

- `vanilla`: `0/29` corrected
- `exit`: `9/29` corrected
- `redirect`: `28/29` corrected
- `always_reflect`: `26/29` corrected

这里最重要的经验对比是：

- early exit 单独较弱
- redirect 很强
- redirect 可以优于 reflection-style baseline
- 下一个关键 control 是 `random redirect`，用来检验 transition-aware timing 是否真的比 prompt 本身更重要

### Part 5：部署故事

- BF16 pilot 用来建立机制。
- quantization 应当被看成 deployment stress test，而不是自动升成主创新点。
- reviewer-safe 的比较方式，是在同一 protocol 下对比 `BF16` 和 `AWQ-Int4`。
- 如果效果在 4 个 viable categories 上都稳定，quantization 可以再往上提。
- 如果效果不稳定，它就应该留在 secondary table，不要让整篇 paper 绑死在这件事上。

## 这篇论文必须满足什么

下面这些基本上不能退：

1. selective-intervention policy 在 4 个 viable categories 上，utility-harm tradeoff 仍然为正。
2. 在 end-to-end 口径下，它的 trigger cost 低于 always-reflect。
3. detection 数字必须用 sample-grouped evaluation，不能再用 trajectory-random CV。
4. BARR 不能明显伤害原本已经正确的样本。
5. quantization 可以增强论文，但前提是 `BF16 vs AWQ-Int4` 在同一 protocol 下稳定成立。

## 不该 oversell 什么

- 不要把当前证据讲成“所有类别都已经很稳”，因为最强证据目前只集中在 4 个 viable categories。
- 不要把 pooled shared strict-online 的 AWQ 结果讲成强正面结果，因为现在它的 trigger rate 和 utility 基本都是 0。
- 不要把 transition-specificity 写得过强，因为 sample-grouped holdout 下 matched non-transition control 也不弱。
- 不要把 LOCO 写成 BF16 上的决定性测试，因为 positive count 还偏小。
- 不要过度强调 `position + hidden` 明显优于 `hidden_only`，因为 held-out gap 现在几乎没有。
- 不要过度强调当前 always-reflect 的 token efficiency，因为那套 baseline 现在还不够强。

## reviewer-safe claim 模板

更安全的写法接近：

> 我们发现，reasoning model 的 fairness failure 往往集中在 transition point 附近；在这些位置上，biased trajectory 更容易被检测到，也更容易被干预。基于这一结构，BARR 可以选择性地重定向高风险 reasoning path，并且比 post-hoc reflection 更高效地改善 fairness，尤其是在部署压力较大的 setting 中。

同时最好配一句 limitation，例如：

> 当前评估主要聚焦于 ambiguous QA，因为这是 bias 最容易被触发的设置；把这个框架扩展到更开放式的 generation 任务，仍然是未来工作。

应避免写成：

> 我们发现了隐藏的 bias circuit。

## 优先级顺序

### Priority 1

- 用冻结的 held-out split 做 sample-grouped detection evaluation
- 完成 4 个 viable categories 的 selective-intervention 主表

### Priority 2

- 在同一 protocol、同 4 个类别上做 reviewer-safe 的 `BF16 vs AWQ-Int4` 对比
- 把 always-reflect baseline 做强
- 在 all samples 上补 end-to-end trigger evaluation

### Priority 3

- 做 CBBQ 中文验证

### Priority 4

- 在更大的 AWQ biased set 上跑 LOCO
- 如果还有时间，再看 StereoSet

## 目标表格

### Table 1

4 个 viable categories 的主 policy 表：

- `age`
- `disability_status`
- `religion`
- `ses`

比较的 policy：

- Vanilla
- Early Exit
- Random Redirect
- Blanket Redirect
- Always-Reflect
- BARR

### Table 2

在同一 protocol 下，对 all samples 统一报：

- `correction`
- `harm`
- `trigger_rate`
- `net_benefit`
- `avg_extra_tokens`

### Table 3

deployment stress-test 表：

- `BF16` vs `AWQ-Int4`
- 相同 protocol
- 相同 4 个 viable categories

### Table 4

detection validation 表：

- sample-grouped AUROC
- transition vs matched control
- 可选地比较 position-only vs position+hidden

## 接下来立刻要做的实验

1. 用 `sample_id` 分组重算 sample-grouped detection。
2. 把论文主表范围冻结到 4 个 viable categories，而不是所有类别。
3. 把 always-reflect baseline 做成一个真正强的 baseline。
4. 在 all samples 上补 trigger rate、token cost、collateral harm 的 end-to-end 评估。
5. 在同 4 个类别上做 reviewer-safe 的 `BF16` 对 `AWQ-Int4` 对比。

## 当前底线判断

这个项目已经有一个可信的 EMNLP paper seed。

BF16 pilot 现在已经不再是在问 “BARR 存不存在”。
它真正开始问的是：完整的 deployment story 能不能撑住：

- 收窄后的 4-category 主表范围
- 更公平的 baselines
- end-to-end trigger accounting
- quantization 作为 stress test，而不是被强行写成唯一 novelty
