# AI_COLLAB_WORKFLOW

## 目标

在 VS Code 中让 **Codex / Claude Code / GitHub Copilot** 协同工作，并尽可能减少 Claude token 消耗。

核心原则：

- **Codex 负责默认 planning、执行推进、阶段总结**
- **Claude 只做关键评审，不做每轮常驻 PM**
- **Copilot 只做局部实现和编辑器内补全**
- **只有出现分歧、风险、架构问题时才升级到 Claude**

---

## 角色分工

### 1. Codex

默认主调度。

负责：
- 阅读相关代码并总结现状
- 产出最小可执行计划
- 拆分任务和执行顺序
- 批量修改、多文件改动、规则化重构
- 每轮结束后写 `progress` 和下一步建议
- 判断是否需要 Claude 介入

不负责：
- 最终架构拍板
- 高成本方案评审

### 2. Claude Sonnet 4.6

默认评审模型。

负责：
- 评估 Codex 提出的候选方案
- 选择最优实施路径
- 输出验收标准、风险点、回滚点
- 明确下一步应该交给 Codex 还是 Copilot

适用场景：
- 需要一个完整但成本可控的方案
- 有 2~3 个实现路径需要比较
- 中等复杂度重构

### 3. Claude Opus 4.6

仅在必要时升级。

负责：
- 高复杂架构判断
- 隐性副作用较多的重构
- Sonnet 无法稳定收敛的问题

使用门槛：
- 核心模块大改
- 认证、状态管理、数据流复杂变更
- 一次决策错误成本很高

### 4. GitHub Copilot

局部实现助手。

负责：
- 小函数
- 当前文件内补全
- UI 微调
- 小范围 bug fix
- 测试样例、mock、注释补全
- 边界清晰的单文件或小范围多文件实现
- 已经确定方案后的中低风险代码生成

不负责：
- 全局规划
- 跨文件设计决策
- 架构选择

补充说明：
- GitHub Copilot 当前能力不应被低估
- 在实现边界清晰、方案已经冻结的任务上，它可以承担质量不错的执行工作
- 尤其适合已经由 Codex 明确输入输出、验收标准和修改范围的实现切片

---

## 默认协作流程

## 阶段 1：Codex 先做低成本 planning

先让 Codex：

1. 阅读相关代码
2. 总结当前现状
3. 输出 1 个最小可执行 slice
4. 标记风险点
5. 判断是否需要 Claude

### 给 Codex 的提示词

```text
先不要直接大改代码。

请先完成：
1. 阅读与当前任务相关的代码和文档
2. 总结当前实现、限制和风险
3. 提出一个最小可执行 slice
4. 说明应该交给 Codex、Claude 还是 Copilot
5. 如果需要 Claude，请输出压缩版 handoff，不要长篇重述背景

目标：尽可能减少 Claude token 消耗。
```

---

## 阶段 2：只有必要时才交给 Claude

当 Codex 认为需要评审时，把压缩后的 handoff 发给 Claude。

### 默认优先级

- 普通方案评审：**Claude Sonnet 4.6**
- 高风险、高复杂问题：**Claude Opus 4.6**

### 给 Claude 的提示词

```text
你不是默认执行者，而是关键评审者。

请基于以下压缩 handoff：
1. 选择最优方案
2. 给出实施顺序
3. 明确哪些步骤交给 Codex
4. 明确哪些步骤交给 GitHub Copilot
5. 给出验收标准、风险点、回滚点
6. 避免重复背景，不要长篇重述
```

### 要求 Claude 输出必须包含

- 推荐方案
- 不推荐方案及原因
- 执行顺序
- **交给 Copilot 还是交给 Codex**
- 验收标准
- 风险与回滚点

---

## 阶段 3：执行阶段尽量不再调用 Claude

执行时按下面路由：

### 交给 Copilot

适合：
- 小函数
- 单文件修改
- 样式微调
- 小测试
- 当前编辑区域补全

### 交给 Codex

适合：
- 多文件修改
- 批量替换
- 重构
- 类型统一
- 规则化修改
- 生成阶段总结和下一步计划

### 不回 Claude 的条件

如果下面都成立，就不要回 Claude：

- 没有架构分歧
- 没有新风险暴露
- 没有偏离原方案
- 验收标准仍然可满足

### 调用 Copilot 前的协作约定

如果某一步明显更适合 GitHub Copilot：

- Codex 需要先明确告知用户
- 说明为什么这一步适合交给 Copilot 而不是继续由 Codex 执行
- 说明交给 Copilot 的具体范围应尽量局部、可控
- 如果这一步是“方案已定、实现边界清晰、主要是执行密集型编码”，应优先考虑 Copilot
- 如果这一步仍然涉及实验路线选择、指标解释、主线取舍，仍由 Codex 主导

也就是说：
- Codex 可以默认主调度
- 但不能在未说明的情况下把关键步骤默认为 “交给 Copilot”

---

## 阶段 4：Codex 负责复盘和二次规划

每轮代码改完后，让 Codex 输出：

- 已完成内容
- 修改文件
- 与原方案的偏差
- 当前风险
- 下一步建议
- 是否需要 Claude 再评审

### 给 Codex 的复盘提示词

```text
请基于刚完成的修改输出：
1. 已完成内容
2. 修改的文件
3. 与原计划的偏差
4. 当前遗留风险
5. 下一步最小可执行 slice
6. 是否需要再交给 Claude 评审

要求：结论优先，简洁，不重复背景。
```

---

## 模型选择规则

### Claude 选择规则

#### 用 Sonnet 4.6

- 默认完整方案评审
- 中等复杂度功能设计
- 一般重构方案判断
- 需要较高质量但不值得上 Opus 的情况

#### 用 Opus 4.6

只有满足任一条件才升级：

- 涉及核心架构调整
- 多个方案 trade-off 很复杂
- 风险不可逆
- Sonnet 输出不稳定或不够深
- 失败成本很高

### GitHub Copilot 模式选择建议

#### 用 GPT-5.3 Code Medium

适合：
- 小块代码生成
- 小函数
- 单文件修改
- 快速测试样例
- 当前上下文明确的实现任务

#### 用 GPT-5.4 Low / Medium / High / Extra High

建议：

- **Low**：简单补全、小修复、低成本尝试
- **Medium**：常规单文件任务、普通实现
- **High**：跨文件但仍然边界清晰的任务
- **Extra High**：较复杂逻辑实现、重要重构前的高质量生成

### 简化决策

- **小改动** → Copilot GPT-5.3 Code Medium 或 GPT-5.4 Low/Medium
- **多文件执行** → Codex
- **方案评审** → Claude Sonnet
- **复杂架构** → Claude Opus

---

## 推荐的仓库文件

建议固定这 3 个文件：

### `docs/ai/current-task.md`

记录：
- 当前任务
- 范围
- 不可触碰边界
- 验收标准

### `docs/ai/progress.md`

由 Codex 更新：
- 已完成内容
- 修改文件
- 风险
- 下一步建议

### `docs/ai/handoff-to-claude.md`

只放压缩信息：
- 背景摘要
- 当前方案
- 实际偏差
- 关键文件
- 需要 Claude 回答的 2~3 个问题

---

## Claude 省 token 规则

1. **不要把整个仓库直接丢给 Claude**
2. **先让 Codex 压缩上下文**
3. **Claude 只看 handoff，不看全量历史**
4. **Claude 第一次出完整方案，后续只做 checkpoint**
5. **没有偏差就不要回 Claude**
6. **让 Codex 负责 progress 和阶段总结**
7. **只把真正需要判断的问题交给 Claude**

---

## 标准循环

```text
Codex 读代码和 planning
→ 如有必要，压缩后交给 Claude 评审
→ Claude 指定执行路线与分工
→ Codex / Copilot 执行写代码
→ Codex 输出 progress 和调整后的 plan
→ 仅当出现偏差或风险时再回 Claude
```

---

## 最短操作版

### Step 1：先问 Codex

```text
先阅读相关代码，输出一个最小可执行 slice，并判断是否需要 Claude 评审。
```

### Step 2：如果需要 Claude，让 Codex 生成 handoff

```text
请把当前任务压缩成给 Claude 的 handoff，控制在必要信息内，并明确希望 Claude 回答的问题。
```

### Step 3：把 handoff 发给 Claude

```text
请基于这个 handoff 选择最优方案，并明确哪些步骤交给 Codex，哪些交给 GitHub Copilot。
```

### Step 4：回到执行

- 多文件/批量修改 → Codex
- 局部实现/补全 → Copilot

### Step 5：让 Codex 复盘

```text
请总结当前 progress、偏差、风险，并给出下一轮最小可执行计划。
```

---

## 一句话原则

**Codex 做默认调度和复盘，Claude 做关键评审，Copilot 做局部实现。没有架构分歧，就不要反复调用 Claude。**
