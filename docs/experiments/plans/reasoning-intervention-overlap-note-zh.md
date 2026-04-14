# Reasoning Intervention 撞车风险对照笔记

## Related notes
- [Docs Index](../../index.md)
- [Week 1 Transition-Probe Plan](./week1-transition-probe.md)
- [Current Pilot Scope](../../progress/current-pilot-scope.md)
- [BARR Mainline Claim](../../research/framing/barr-mainline.md)
- [参考文献 PDF](../../references/8574_Wait_am_I_Being_Fair_Char.pdf)

## 这份笔记回答什么问题

这份笔记用于回答两个问题：

1. 论文《Wait, am I Being Fair?》和我们当前的 Phase C idea 有没有明显撞车？
2. 如果有重叠，我们后续应该把 claim 收到哪里，才能避免“别人已经做过”的风险？

结论先写在前面：

- **有重叠，但不是完全一样。**
- 他们已经做了 **reasoning-time injection**，也就是在模型推理过程中插一句反思话。
- 我们如果只做“在某个位置插一句反思 prompt”，那会和他们明显重叠。
- 我们真正还能站得住的差异点，是 **transition-aware timing**：干预时点不是拍脑袋选的，而是由内部状态的 transition signal 决定的。

---

## 他们到底做了什么

论文主线很清楚：

- 模型先生成一段 reasoning
- 在 **最终答案输出之前**
- 插入一句短的 reflective cue
- 再让模型继续生成

他们最有代表性的人工短语就是：

`Wait, am I being fair?`

大白话理解：

- 模型先自己想一段
- 快要回答时
- 他们插一句“等一下，我这样公平吗？”
- 看模型会不会因此改口

---

## 他们把这句话插在什么位置

### 主方法里的默认位置

他们正文里写的是：

- 先生成 intermediate reasoning steps
- **before the LLM generates the predicted answer**
- 再插入 phrase

还写了：

- “immediately after the model’s reasoning step”

这说明他们的默认做法不是在 hidden-state 检测到某个内部转折点时插，而是：

**在 reasoning 结束、final answer 出来之前插一次。**

大白话就是：

- 不是中间某个隐状态分岔点
- 而是“快答题前，临门一脚提醒一下”

### 位置 ablation 里测试了哪些位置

他们在附录里专门做了 injection position 的实验，比较了：

- `E`：在 reasoning **末尾**插入
- `E-50`：在 reasoning 结束前 `50` 个 token 插入
- `S+50`：从 reasoning 开头往后 `50` 个 token 插入
- `S+100`：从 reasoning 开头往后 `100` 个 token 插入
- `Rand`：在 reasoning 内 **随机位置** 插入

他们的结论是：

- **`E` 最好**
- `E-50` 次之
- 早插，比如 `S+50`、`S+100`，效果更差
- 随机插也更差

大白话就是：

**他们发现“越接近最终答案再提醒”越有效。**

---

## 他们每条 reasoning 插几次

### 主实验

主实验默认是：

- **每条 reasoning 插 1 次**

也就是：

- 先 reasoning
- 插一句
- 再继续生成到答案

### 频率 ablation

他们还专门测了：

- 随机插 `1` 次
- 随机插 `2` 次
- 随机插 `3` 次

结论是：

- 随机插多次并没有变成更好的方法
- **插在哪里，比插几次更重要**

大白话就是：

- 不是多喊几遍“公平一点”就更有用
- 关键是你在什么时候打断它

---

## 和我们当前 Phase C 有哪些重叠

### 明显重叠的部分

如果我们的方法描述成：

- 在模型 reasoning 过程中
- 插入一句反思或纠偏 prompt
- 看它会不会从 biased 变成更公平的回答

那这和他们已经非常接近。

重叠点包括：

- 都是 **inference-time / reasoning-time intervention**
- 都不改模型参数
- 都是在生成过程里插入一段文字
- 都关心模型能否在推理过程中“回头修正”

### 我们当前版本还多了一个问题

我们之前的 Phase C prompt 里曾经直接写过：

- 如果信息不足，就输出 `Unknown`

这会带来两个问题：

1. 这不只是反思 prompt，而是**直接给答案方向**
2. 这样即使有效，也很难 claim 是 timing 或机制本身的作用

所以旧版结果不能作为严格主结果，只能算 pilot。

---

## 我们还有什么不一样

我们最重要、也最值得保住的点是：

### 1. 我们的时点不是手工 token 位置，而是 transition-aware

他们的位置定义是：

- 结尾
- 结尾前 50 token
- 开头后 50 token
- 开头后 100 token
- 随机

本质上还是 **token-position heuristic**。

我们想做的则是：

- 先用 Phase B 找到内部状态真正发生分岔的位置
- 再围绕这些 transition 点做干预

所以我们的方法更像：

- **state-based timing**

而不是：

- **surface token position timing**

### 2. 我们有一个更明确的 mechanistic claim 候选

他们的主结论更偏行为层面：

- reflective prompt 在 reasoning 末尾插入更有效

我们如果做成功，可以更进一步说：

- 模型在某些内部 transition 点已经开始朝 biased trajectory 分流
- 在这些点附近干预，比拍脑袋选一个 token 位置更有根据

换句话说，他们更像：

- “什么时候提醒比较有用？”

我们更想回答：

- “模型内部什么时候开始拐偏？在那个点附近出手是否更有效？”

---

## 目前可 claim 和不可 claim 的边界

### 现在不能直接 claim 的

如果我们的实验只是：

- 在某个时点插一句 prompt
- 然后模型更常答 `Unknown`

那不能直接 claim：

- 我们发明了 reasoning-time fairness intervention
- 在推理中插一句反思话这件事是新的
- 任何 late-stage intervention 都是我们的贡献

因为这些方向这篇论文已经覆盖得很近了。

### 我们更适合 claim 的

如果后续实验做得干净，可以更稳地 claim：

- **transition-state separation can identify promising intervention windows**
- **transition-aware intervention timing is more principled than generic late-stage injection**
- **the useful timing signal comes from internal state dynamics, not only from surface token position**

如果再做强一点，还可以尝试 claim：

- transition-aligned timing 优于 generic end-of-reasoning injection
- transition timing 能部分解释为什么“末尾插一句”有效

---

## 为了避免撞车，Phase C 应该怎么收缩

建议把后面的 Phase C 明确分成两层。

### 层 1：严格版 timing test

目标：

- 测 timing 本身是否有用

做法：

- 使用 **不提供答案方向** 的 neutral / anti-stereotype reflective cue
- 不出现 `Unknown`
- 不出现 “not enough information, answer Unknown” 这种句子

建议可用的 prompt 风格：

- `Review your reasoning so far. Check whether each step is supported by the given context. Revise if needed.`
- `Review your reasoning so far. Check whether you relied on stereotypes rather than the given context. Revise if needed.`

### 层 2：对照现有文献的 baseline

目标：

- 明确和《Wait, am I Being Fair?》比较

做法：

- 加一个 **end-of-reasoning reflective injection** baseline
- prompt 可以是类似他们的反思句，但不要和我们的主结论混在一起

这样后面就能回答一个很关键的问题：

- **transition-aware timing 是否优于 generic late-stage reflection？**

这比单纯比较 `t-1 / t / t+1 / random` 更有论文价值。

---

## 下一步最值得补的实验

### 实验 1：transition-aware vs end-of-reasoning

比较：

- `transition-aligned`
- `end-of-reasoning`
- `random`
- `no_intervention`

目的：

- 证明我们的提升不是“只要靠后插一句都行”

### 实验 2：neutral cue vs fairness cue

比较：

- neutral reflective cue
- anti-stereotype cue
- direct-answer cue（仅作为辅助，不作为主结果）

目的：

- 区分 timing effect、reflection effect、answer-hint effect

### 实验 3：单次插入 vs 多次插入

虽然这篇论文已经说明“位置比次数更重要”，但我们仍可少量复验：

- transition 点附近插 `1` 次
- transition 点附近插 `2` 次

如果结果也显示“多插没帮助”，那反而能支撑我们把重点放回 timing。

---

## 这篇参考文献给我们的具体启发

这篇《Wait, am I Being Fair?》不只是提醒我们“有撞车风险”，它其实还给了我们几条很有用的实验启发。

### 启发 1：位置确实重要，而且越靠近最终决策越可能有效

他们的结果显示：

- 在 reasoning 末尾插入，效果最好
- 早插或者随机插，效果更差

这说明：

- 干预时机不是一个可有可无的小细节
- timing 本身很可能就是有效性的核心变量之一

这对我们是好消息，因为我们的主线本来就在问：

- **什么时候干预最有效？**

区别在于，我们不应该只满足于“末尾最好”，而是要继续追问：

- **内部 transition 点附近，是否比 generic late-stage 更好？**

### 启发 2：我们必须显式加入 end-of-reasoning baseline

如果我们不加入一个“在 reasoning 末尾插一次 reflective cue”的 baseline，那么后面即使我们看到 transition-aware 方法有效，也很难证明：

- 它是因为 transition-aware
- 而不是因为“反正靠后插一句都有效”

所以后续实验里，`end_of_reasoning` 应该成为一个明确 baseline，而不是只比较：

- `t-1`
- `t`
- `t+1`
- `random`

### 启发 3：提示词要尽量不带答案方向

这篇论文最强的地方之一是：

- 它主要依赖 reflective cue
- 而不是直接告诉模型“答案应该是 Unknown”

这提醒我们：

- 如果 prompt 里直接写 `Unknown`
- 那实验就更像 answer hint，而不是 reflection timing

所以我们后面的主实验应该坚持：

- 不给答案
- 只给反思或证据检查信号

### 启发 4：位置可能比频率更重要

他们发现：

- 随机插 1 次、2 次、3 次都不如插在对的位置

这意味着我们的优先级应该是：

1. 先把 timing 做对
2. 再考虑要不要做多次 intervention

也就是说，当前最值得投资源的不是“插几次”，而是：

- transition 点是不是比 generic 末尾点更有信息价值

### 启发 5：我们可以把他们当成行为层 baseline，把自己定位成机制层 extension

一个比较自然的论文定位方式是：

- 他们回答了：`reasoning-time reflection can help`
- 我们尝试回答：`internal transition states can tell us when reflection should happen`

这样不是跟他们硬碰硬，而是：

- 在他们的行为层发现之上
- 再往前推进一步到时机选择的机制层解释

---

## 当前判断

当前最稳的判断是：

- **有重叠，但不必然撞死。**
- 如果我们只是做“推理中插一句提醒”，那会很像他们。
- 如果我们把重点改成 **internal-state-informed timing**，并且拿它去对比 generic late-stage injection，我们仍然有清晰可讲的空间。

一句话版：

**他们的贡献是“reasoning 末尾插一次 reflective cue 很有用”，我们要保住的贡献应该是“internal transition state 可以告诉我们什么时候插最合适”。**
