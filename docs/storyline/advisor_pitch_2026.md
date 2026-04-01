# BARR 导师汇报稿

Date: 2026-03-31
Target: EMNLP 2026 ARR May cycle

---

## 一句话定位

推理型模型在推理过程中会渐进性地积累偏见，量化部署会加剧这个问题。BARR 是一个推理中途的选择性干预方法，只在检测到高风险时介入，不对每个样本都付出额外代价。

---

## 三段式汇报（每段约 30 秒）

### 一、问题

推理型模型在推理过程中会渐进性地聚合偏见，量化部署会加剧这个问题。现有的纠偏方法要么对所有样本都干预（副作用大），要么完全不干预。缺一个"只在需要时干预"的方案。

### 二、方法

我们发现模型推理中的 transition point（Wait / Hmm / But 这些转折处）是偏见轨迹可检测的关键窗口。BARR 在这些窗口用轻量分类器判断风险，只对高风险样本注入 redirect 提示来纠正推理方向。不需要重新训练，不需要对每个问题都额外反思。

### 三、初步结果

在 Qwen3-8B AWQ-Int4 量化模型的 BBQ 实验上，BARR 在 age 类别的纠偏率 70%，误伤率只有 1.4%，是所有方法里副作用最低的。对比全量 redirect 误伤 43%，对比 always-reflect 误伤 7.8%。目标是投 EMNLP 2026 的 ARR May cycle。

---

## 我们的定位

现有方法要么是全局干预（对所有样本都反思 / 提示），要么是事后干预（等模型想完再纠）。全局干预的问题是副作用大——我们实验发现对所有样本做 redirect 会破坏 44% 原本正确的回答。事后干预的问题是时机太晚——偏见已经在推理链中累积完了。

我们的定位是：**推理中途的选择性干预，只在检测到高风险时介入。**

---

## 检测信号为什么可靠

- Transition point 的 hidden state 做 probe，AUROC 0.96
- Transition point 位置的信号显著强于附近非 transition 位置（0.96 vs 0.86），说明不是随便找个位置都行
- Signal 在量化模型（AWQ-Int4）上同样成立

---

## 核心贡献一句话

这篇论文的贡献是一个实用的 inference-time fairness method，不是一个机制发现。适合投 EMNLP。

---

## 导师可能追问

**"和你第一篇的 self-reflection 有什么区别？"**

第一篇是 always-on 的，每个样本都做反思。这篇的关键进步是 selective——用 detection 决定谁需要干预。而且干预时机更早：在推理中途而非推理结束后。

**"为什么不直接用 always-reflect？"**

因为 always-reflect 对不需要干预的样本也有副作用（disambig harm 7.8%）。在对副作用敏感的部署场景里（比如教育、医疗），BARR 的 1.4% 误伤率是更安全的选择。

**"这个 detection 靠谱吗？"**

目前在 transition point 用 position + hidden state 做 probe，AUROC 0.96。而且 transition point 的信号显著强于附近非 transition 位置（0.96 vs 0.66），说明不是随便找个位置都行。

---

## 当前状态（2026-03-31）

- BF16 + AWQ-Int4 的 detection 信号已验证
- AWQ age 类别 selective trigger 结果已冻结（纠偏 70%，误伤 1.4%，net +30）
- 其余类别正在推进中，AUC 普遍 0.90+，selective trigger 精度待进一步提升
- 下一步：扩展到更多 BBQ 类别，完善 end-to-end token accounting
