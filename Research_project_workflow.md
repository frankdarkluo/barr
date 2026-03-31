# TENNIS_LEVEL AI 工作流说明

这份文件用于直接指导 GitHub Copilot / Codex（`gpt-5.3-codex medium`）在你的 `TENNIS_LEVEL` 仓库里完成以下事情：

1. 规范知识文档目录
2. 每天自动整理当天进展并生成 `progress.md`
3. 自动跳过“当天无有效进展”的情况
4. 自动归档散落的 Markdown 文档
5. 为后续 Obsidian / Claude Code / Codex 协同提供稳定结构

---

# 一、推荐最终目录结构

```text
TENNIS_LEVEL/
  .claude/
  .history/
  .vscode/
  src/
  public/
  scripts/
  supabase/
  docs/
    index.md
    progress/
      2026-03-30.md
      2026-03-31.md
    weekly/
      2026-W14.md
    decisions/
      DEC-001-study-mode-scope.md
      DEC-002-video-diagnosis-direction.md
    features/
      study-mode.md
      remote-session.md
      video-diagnosis.md
    issues/
      issue-data-quality.md
      issue-onboarding-dropoff.md
    roadmap/
      current-quarter.md
      backlog.md
    research/
      study_snapshot_note.md
      study_remote_migration_checklist.md
    templates/
      daily-progress-template.md
      weekly-review-template.md
      decision-template.md
    prompts/
      DAILY_PROGRESS_PROMPT.md
      ORGANIZE.md
      WEEKLY_REVIEW_PROMPT.md
  AGENTS.md
  README.md
  package.json
```

---

# 二、每个文件夹放什么

## `docs/progress/`
每天一篇进展记录，文件名使用日期，例如：

- `2026-03-30.md`
- `2026-03-31.md`

这些文件是原始项目演进记录，重点写：

- 今天做了什么
- 和昨天相比真正变化了什么
- 当前卡点是什么
- 下一步打算做什么

## `docs/weekly/`
每周总结，只保留浓缩版结果：

- 本周关键推进
- 本周新增决策
- 本周核心问题
- 下周重点

## `docs/decisions/`
记录关键决策，不要和 daily progress 混在一起。

每篇一条正式决策，例如：

- 为什么做 `study mode`
- 为什么调整视频诊断方向
- 为什么修改数据结构

## `docs/features/`
每个功能一个专题页，用来持续更新。

例如：

- `study-mode.md`
- `video-diagnosis.md`
- `remote-session.md`

每个功能页长期维护：目标、当前状态、已完成、待解决、相关决策。

## `docs/issues/`
记录持续性问题或风险，不要只埋在 daily progress 里。

例如：

- 数据质量问题
- onboarding 转化问题
- 远程同步不稳定

## `docs/roadmap/`
放阶段计划和 backlog。

## `docs/research/`
放研究笔记、迁移清单、调研记录、快照文档。

## `docs/templates/`
放固定模板，方便 AI 和你自己复用。

## `docs/prompts/`
放给 Copilot / Codex / Claude Code 的提示词文件。

---

# 三、你现在的文件怎么归位

建议按下面方式迁移：

## 迁移到 `docs/research/`

- `docs_local/STUDY_REMOTE_MIGRATION_CHECKLIST...`
- `docs_local/STUDY_SNAPSHOT_NOTE.md`

## 迁移到 `docs/features/` 或 `docs/research/`

- `docs_local/STUDY_MODE.md`

如果它是功能说明，放 `docs/features/study-mode.md`。
如果它更像研究记录，放 `docs/research/study_mode.md`。

## 迁移到 `docs/index.md` 或 `docs/weekly/`

- `PROJECT_PROGRESS_SUMMARY.md`

如果它是当前项目总览，核心内容合并进 `docs/index.md`。
如果它是阶段总结，保留为某一期 `docs/weekly/`。

## 建议重命名或归档

- `requirement.txt` → 建议改为 `docs/roadmap/requirements.md`
- `Efficiency.md` → 根据内容放到 `docs/research/` 或 `docs/issues/`

---

# 四、`prompt.md` 放哪里？

建议统一放在：

```text
docs/prompts/
```

具体建议：

- 每日整理 prompt：`docs/prompts/DAILY_PROGRESS_PROMPT.md`
- 自动归档 prompt：`docs/prompts/ORGANIZE.md`
- 每周复盘 prompt：`docs/prompts/WEEKLY_REVIEW_PROMPT.md`

这样做有三个好处：

1. Obsidian 能直接管理这些提示词
2. VS Code / Copilot / Codex 能直接读取这些 Markdown 文件
3. 后续你可以不断迭代 prompt，而不是每次重新写

---

# 五、`DAILY_PROGRESS_PROMPT.md` 内容

下面这段可以直接保存为：

```text
docs/prompts/DAILY_PROGRESS_PROMPT.md
```

---

# DAILY_PROGRESS_PROMPT

你现在在 `TENNIS_LEVEL` 仓库中工作。请自动整理“今天”的项目进展，并生成或更新当天的 daily progress 文档。

## 目标

请基于今天实际发生的代码、文档、配置、脚本、数据库、研究记录等变更，整理出一份高质量的当天进展记录，保存到：

`docs/progress/YYYY-MM-DD.md`

其中日期使用今天的本地日期。

## 核心要求

1. 只根据“今天真实发生的变更”来写，不要凭空脑补。
2. 如果今天没有任何有意义的实际进展，不要创建空文档，直接跳过。
3. 不要把机械性噪音写进进展，例如：
   - 纯格式化
   - 无意义重排
   - lockfile 轻微变动
   - 自动生成但没有业务价值的改动
4. 重点提炼“相对于之前，今天真实推进了什么”。
5. 输出要面向项目演进，而不是代码 diff 罗列。

## 请检查的范围

优先检查以下内容：

- `src/`
- `public/`
- `scripts/`
- `supabase/`
- `docs/`
- 根目录中的重要 Markdown 文档
- 与产品方向、研究、实验、数据结构、部署、诊断能力有关的文件

## 建议参考信息

请综合以下信号判断今天是否有有效进展：

- 今日 git diff
- 今日新增或修改文件
- 今日提交记录（如果可用）
- 今日文档更新
- 今日 SQL / schema 变化
- 今日功能实现或逻辑调整

## 跳过规则

如果今天满足以下任一情况，则不要生成 `docs/progress/YYYY-MM-DD.md`：

1. 没有任何文件变更
2. 只有格式化、注释微调、无意义重命名
3. 只有依赖安装或构建产物变化，没有项目层面的真实推进
4. 无法提炼出对产品、功能、研究、架构、流程有意义的变化

## 输出格式

请严格使用下面结构：

```md
# YYYY-MM-DD Progress

## 今日核心进展
- 
- 
- 

## 具体变化
### 产品/功能
- 

### 技术实现
- 

### 文档/研究
- 

## 与昨天相比的真实变化
- 

## 当前问题或风险
- 

## 下一步建议
- 
- 
```

## 写作要求

1. 语言简洁、具体、可追踪。
2. 优先写“结果”和“影响”，少写空泛过程描述。
3. 如果某部分没有内容，可以省略该小节，但不要编造。
4. 如果某项变化明显属于某个 feature / decision / issue，请在文中提到对应主题。
5. 如果今天的变化值得沉淀为长期文档，请顺手建议：
   - 更新哪个 `docs/features/*.md`
   - 新建哪个 `docs/decisions/*.md`
   - 更新哪个 `docs/issues/*.md`

## 额外动作

生成 daily progress 后，请再执行以下检查：

1. 如果今天出现新的关键产品决策，建议新建一条 decision 文档。
2. 如果今天明显推进了某个已有功能，建议更新对应 feature 文档。
3. 如果今天暴露了持续性问题，建议更新 issue 文档。
4. 不要自动大范围改写无关文件。

最终目标：
这份 daily progress 必须能让人一眼看出“今天这个项目到底真实往前走了什么”。

---

# 六、`ORGANIZE.md` 内容

下面这段可以直接保存为：

```text
docs/prompts/ORGANIZE.md
```

---

# ORGANIZE

你现在在 `TENNIS_LEVEL` 仓库中工作。请把当前仓库中的项目文档整理成一个适合 Obsidian + VS Code + AI 协同的结构，但不要误伤代码文件。

## 目标

建立稳定的知识文档结构，使项目进展、功能专题、决策、问题、路线图能够持续沉淀。

## 你要做的事情

### 1. 创建以下目录（如果不存在）

```text
docs/progress/
docs/weekly/
docs/decisions/
docs/features/
docs/issues/
docs/roadmap/
docs/research/
docs/templates/
docs/prompts/
```

### 2. 创建以下基础文件（如果不存在）

- `docs/index.md`
- `docs/templates/daily-progress-template.md`
- `docs/templates/weekly-review-template.md`
- `docs/templates/decision-template.md`
- `docs/prompts/DAILY_PROGRESS_PROMPT.md`
- `docs/prompts/ORGANIZE.md`
- `docs/prompts/WEEKLY_REVIEW_PROMPT.md`

### 3. 迁移现有文档

按内容语义做迁移，不要机械移动：

- `docs_local/` 中的研究/快照/迁移类文档 → `docs/research/`
- 功能说明类文档 → `docs/features/`
- 项目阶段总结类文档 → `docs/weekly/` 或合并进 `docs/index.md`
- 根目录中散落的说明文档 → 根据内容归档到合适目录

### 4. 文件命名规范化

统一使用：

- 小写
- 单词之间用连字符 `-`
- 日期文件使用 `YYYY-MM-DD.md`
- decision 文件使用 `DEC-xxx-name.md`

### 5. 生成 `docs/index.md`

`docs/index.md` 应该包含：

- 项目简介
- 当前重点
- 最近 progress 列表
- features 入口
- decisions 入口
- issues 入口
- roadmap 入口

### 6. 不要碰这些内容

以下目录和文件不要因为“整理文档”被大范围改写：

- `src/`
- `public/`
- `scripts/`
- `supabase/`
- 配置文件
- 依赖文件
- 构建产物

除非只是为了在文档中引用它们。

## 产出要求

1. 优先保证结构清晰，而不是一步到位完美。
2. 保留原始信息，不要因为重组而丢内容。
3. 如果某个文件难以判断归属，优先放到 `docs/research/`。
4. 所有新建文档都用 Markdown。
5. 尽量减少无意义改名，避免破坏已有引用。

最终目标：
让 `docs/` 成为这个项目真正的知识入口和项目记忆系统。

---

# 七、`WEEKLY_REVIEW_PROMPT.md` 内容

下面这段可以直接保存为：

```text
docs/prompts/WEEKLY_REVIEW_PROMPT.md
```

---

# WEEKLY_REVIEW_PROMPT

你现在在 `TENNIS_LEVEL` 仓库中工作。请基于本周所有 daily progress，生成一份周总结。

## 目标

读取：

- `docs/progress/` 中本周的全部日记录

输出到：

- `docs/weekly/YYYY-Www.md`

其中 `YYYY-Www` 使用本周周数，例如 `2026-W14.md`。

## 输出结构

```md
# YYYY-Www Weekly Review

## 本周最重要的进展
- 
- 
- 

## 功能推进
- 

## 关键决策
- 

## 暴露的问题 / 风险
- 

## 本周形成的结论
- 

## 下周建议重点
- 
- 
```

## 要求

1. 只基于已有 progress 内容总结，不要虚构。
2. 优先提炼“本周方向真的发生了什么变化”。
3. 如果只是重复性推进，要压缩表达，不要堆砌。
4. 如果本周出现值得长期保留的结论，建议同步更新 feature / decision / issue 文档。

---

# 八、3 个可直接复制给 Claude Code / Codex 的提示词

## Prompt 1：每日整理进展

```text
请读取当前仓库今天的实际变更，并判断是否存在有意义的项目进展。

如果有：
1. 生成或更新 docs/progress/YYYY-MM-DD.md
2. 按“今日核心进展 / 具体变化 / 与昨天相比的真实变化 / 当前问题或风险 / 下一步建议”的结构输出
3. 重点提炼真实推进，不要只罗列 diff
4. 如有必要，指出应该更新哪个 feature / decision / issue 文档

如果没有有意义进展：
- 不创建空文件
- 直接告诉我今天可以跳过 daily progress
```

## Prompt 2：整理仓库文档结构

```text
请把当前仓库中的文档整理为一个适合 Obsidian + VS Code + AI 协同的 docs 系统。

目标结构包括：
- docs/progress
- docs/weekly
- docs/decisions
- docs/features
- docs/issues
- docs/roadmap
- docs/research
- docs/templates
- docs/prompts

请完成：
1. 创建缺失目录
2. 迁移现有 markdown 到合适位置
3. 生成 docs/index.md
4. 保留原始信息，不要误改代码目录
5. 文件命名尽量规范为小写加连字符
```

## Prompt 3：从最近几天进展里抽取长期知识

```text
请读取 docs/progress/ 最近 3 到 7 天的记录，并帮我做知识沉淀。

请完成：
1. 找出真正发生变化的功能方向
2. 如果有新的产品决策，生成 docs/decisions/ 下的新文档
3. 如果某个功能说明已经明显变化，更新 docs/features/ 对应页面
4. 如果出现持续性阻塞或风险，更新 docs/issues/ 对应页面
5. 最后给出一段简短总结：最近这几天项目真正往前走了什么
```

---

# 九、建议你实际怎么用

## 日常

每天定时运行：

- `docs/prompts/DAILY_PROGRESS_PROMPT.md`

目的：
自动判断当天是否有真实进展，有则生成 `docs/progress/当天日期.md`，无则跳过。

## 首次整理仓库

运行：

- `docs/prompts/ORGANIZE.md`

目的：
把现在散落的文档先收拢成稳定结构。

## 每周一次

运行：

- `docs/prompts/WEEKLY_REVIEW_PROMPT.md`

目的：
压缩一周内容，形成周级别视图。

## 隔几天一次

运行上面的 Prompt 3。

目的：
不要只积累 progress，还要持续抽取 decision / feature / issue。

---

# 十、最实用的落地建议

如果你现在想最小成本启动，那就按这个顺序：

1. 先让 Copilot / Codex 执行 `ORGANIZE.md`
2. 以后每天定时执行 `DAILY_PROGRESS_PROMPT.md`
3. 每周执行一次 `WEEKLY_REVIEW_PROMPT.md`
4. Obsidian 主要打开 `docs/` 目录来看知识结构
5. VS Code 继续打开整个仓库做开发

这样你就不是“堆文档”，而是在慢慢形成：

- 时间线
- 决策链
- 功能演进页
- 问题沉淀
- 周级总结

这才是 Obsidian 和 AI 结合在你这个项目里的真正价值。