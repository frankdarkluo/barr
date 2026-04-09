# Daily Research Log Skill

> 用途：让 Claude Code / Codex 自动整理每日实验记录，生成结构化的日报与周报。  
> 适用：ML/NLP 实验，尤其是每天产出大量中间结果的 Agent 驱动型项目。

---

## 一、筛选原则：什么结果值得汇报

| 汇报？ | 类型 | 判断标准 |
|:------:|------|----------|
| **是** | 关键结果 | 性能突破、发现新问题、验证/推翻假设 |
| **是** | 方案变更 | 中间结果导致实验方案调整（需标注 ⚠️） |
| 视情况 | 调参/debug | 仅当揭示了可复用的规律时汇报 |
| **否** | 中间态 | 未收敛、探索性跑了几个 epoch 的结果 |

---

## 二、每日实验记录模板

```markdown
# 实验日志 — YYYY-MM-DD

## Purpose
一句话：今天做了什么、想验证什么。

## Protocol
- **数据集**：名称、规模（train/valid/test）、特殊处理（dedup/overlap 清理/tokenization）
- **模型**：架构、关键超参（lr, batch size, epochs, 其他影响结果的参数）
- **步骤**：简要流程，1-3 句话即可；如果沿用之前的 protocol，注明「同 MM/DD」

## Results

<!-- 按需选择一种或多种展示方式，表格优先 -->

**定量结果**
| Model | BLEU-2 | BLEU-4 | DIST-1 | DIST-2 | Note |
|-------|--------|--------|--------|--------|------|
| Baseline [来源] | | | | | |
| 本次实验 | | | | | |

> 指标格式：同一表内统一用小数或百分比，表头注明。

**Case Study**（若有）
| Input | Output | Reference | Comment |
|-------|--------|-----------|---------|
| ... | ... | ... | ... |

**趋势/图**（若有）
> 用 `[图：简要描述]` 占位，后续替换截图。若无图，省略此节。

## Observation
客观描述结果呈现的现象，不推断原因。每条一句话。
- ...
- ...

## Hypothesis
基于 Observation 提出可能的解释，标注置信度。
- **[高]** ...
- **[中]** ...
- **[低/待验证]** ...

## Next Steps
- [ ] 行动项 1
- [ ] 行动项 2
```

---

## 三、每周汇总模板

```markdown
# 周报 — YYYY 第 WW 周（MM/DD ~ MM/DD）

## 一句话总结
本周最重要的发现或进展。

## 时间线
| 日期 | 主题 | 关键结论 | 方案变更？ |
|------|------|----------|:----------:|
| MM/DD | ... | ... | ✅ / — |

## 核心指标对比
| 条件 | Metric A | Metric B | 说明 |
|------|----------|----------|------|
| ... | ... | ... | ... |

## 假设验证跟踪
| 假设 | 状态 | 证据来源 |
|------|:----:|----------|
| ... | ✅ 已验证 / ❌ 推翻 / ⚠️ 部分支持 | MM/DD 实验 |

## 当前状态
- **已完成**：...
- **进行中**：...
- **受阻**：...

## 下周计划
1. ...
2. ...
```

---

## 四、调用 Prompt

以下 prompt 供 Claude Code / Codex 自动化调用：

```
你是科研实验记录整理助手。根据今天的原始实验日志，按 `daily-research-log-skill.md` 的模板生成结构化日报。

规则：
1. 只汇报推动项目进展的结果；方案调整标注 ⚠️
2. 结果优先用 Markdown 表格；趋势/分布用 [图：描述] 占位
3. Observation 只写客观现象；Hypothesis 标注置信度
4. 同一表内指标格式统一（小数或百分比）
5. 参考数据标注来源

原始记录：
---
[粘贴]
---
```

---

## 五、示例（基于 PDF 中 2021-10-21 记录）

### 实验日志 — 2021-10-21

#### Purpose
移除 DailyDialog test set 中 segmentation 不一致的重复样本，评估 T5-base 的高 BLEU 是否部分源于 train-test overlap。

#### Protocol
- **数据集**：DailyDialog（Yanran Li et al.），移除 test 中 19 条近重复样本（~0.5%）
- **模型**：T5-base（Wen），epoch 918/972；预处理沿用 Hareesh 方案（数字→`NUM`）

#### Results

| Model | Epoch | BLEU-2 | BLEU-4 | DIST-1 | DIST-2 |
|-------|-------|--------|--------|--------|--------|
| LSTM w/ attn [Hareesh] | ?/200 | 3.96 | 0.85 | 4.4 | 27.5 |
| T5-base [Wen] | 918/972 | **7.295** | **3.386** | 7.818 | 38.099 |

**Case Study**

| Train | Test | Overlap |
|-------|------|---------|
| what does it **say**? → it says no smoking here. | what does it **says**? → it says no smoking here. | ~100% |
| how much do the roses cost? → NUM a dozen. | what would the roses cost me → theyre only NUM a dozen | ~100% |

#### Observation
- 移除 19 条后，T5-base BLEU-2 仍显著高于 LSTM（7.30 vs 3.96），差距未消弭。
- Case study 显示 train/test 存在仅有词形差异（say/says）的近乎完全重复对。
- 被移除样本的 overlap 来源主要是 segmentation 不一致，而非语义重复。

#### Hypothesis
- **[高]** T5-base 凭预训练优势本身就优于 LSTM，BLEU 差距不完全由 overlap 解释。
- **[中]** Segmentation 不一致导致的伪重复低估了真实 overlap 规模，需系统性分析。
- **[待验证]** Word-level overlap ratio 可量化 train-test 相似度分布，找到合理过滤阈值。

#### Next Steps
- [ ] 复现 Hareesh 同款 LSTM，对齐 baseline
- [ ] DailyDialog 全量 train-test overlap 分布统计
- [ ] 探索 word overlap ratio threshold 选取策略

---

## 六、补充说明

1. **多方向实验**：同一天做了 A、B 两个方向，拆成两个 `## Purpose` section，保持同一文件。
2. **图片处理**：TensorBoard/WandB 截图用 `![描述] path-to-image` 形式嵌入；暂无截图用 `[图：描述]` 占位。
3. **周报节奏**：建议周五晚或周一早运行，输入为该周所有日报 `.md` 文件。
4. **文件命名**：日报 `YYYY-MM-DD.md`，周报 `YYYY-MM-DD-weekly.md`；若需要中英文平行笔记，使用相同 basename 加语言后缀。
