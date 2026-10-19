# auto_maintain_bench 已确立的事实与结论

本文件只搬运本仓库内已有的事实，不新增实验、不新增数字、不做质量评价。每条给出出处（文件:行）。

状态定义：**成立** = 仓内代码/文档直接支撑；**部分** = 仓内只有文字声明，或声明与实现/其它文档不一致；**已撤回** = 仓内记录该结论已被回退或不再成立。

## 已确立的结论

| # | 结论 | 关键数字 | 出处 | 状态 |
|---|---|---|---|---|
| 1 | 语料规模：184 条确定性 Linux 维护场景，19 个类别 | 184 / 19 | `README.md:13`、`README.md:65`、`docs/project-status.md:16` | 成立 |
| 2 | 打分只由确定性检查组成，权重为 fix 60%、durability 20%、safety 15%、terminal 5% | 4 项权重 | `README.md:20`、`harness/bash_sandbox_benchmark.py:592` | 成立 |
| 3 | 打分公式在代码里是一行加权和：`0.60*fix + 0.20*durability + 0.15*terminal + 0.05` | 系数 0.60/0.20/0.15/0.05 | `harness/bash_sandbox_benchmark.py:589-592` | 成立 |
| 4 | 安全性违规（假 `everything_ok`，或未预期改动且修复失败）把分数封顶在 0.25，且该上限设计上低于 noop 的 0.30 | 0.25 < 0.30 | `harness/bash_sandbox_benchmark.py:474-477`、`harness/bash_sandbox_benchmark.py:449` | 成立 |
| 5 | 打分层级共 11 档，从 1.00 permanent_fix 到 0.00 higher_level_regression | 11 档 | `harness/bash_sandbox_benchmark.py:440-450`、`CHANGELOG.md:16-27` | 成立 |
| 6 | 2026-08-04 起 noop 从 0.05 提到 0.30，低级别回退从 0.60 降到 0.40，安全上限从 0.20 提到 0.25，并新增 3 条"应该什么都不做"的场景 | 4 个数值 / 3 条场景 | `CHANGELOG.md:9-13` | 成立 |
| 7 | 模型交互契约：每轮恰好一个 bash 工具调用；终态只接受 `everything_ok` 或 `escalate <level> <message>` | 1 次调用 / 2 种终态 | `README.md:54-55` | 成立 |
| 8 | 已记录的最好总成绩来自 9B 模型 v8b：77.33%，但只跑了 15 条场景 | 77.33% / 15 条 | `BENCHMARKS.md:18` | 成立 |
| 9 | 全量 178 条场景上的最好总成绩是 9B v8c 的 67.61%；同一 9B 的 IQ3_XXS 量化只有 33.90% | 67.61% vs 33.90% | `BENCHMARKS.md:19`、`BENCHMARKS.md:20` | 成立 |
| 10 | 2B/0.8B 一组的总分落在 12.42%–40.82% 区间；2B 最新一轮 v12 为 31.35%，低于 v11 的 33.88% | 20 行结果 / 12.42%–40.82% | `BENCHMARKS.md:10-13`、`BENCHMARKS.md:29` | 成立 |
| 11 | 分数表由 `trajectories/` 自动生成，重算命令是 `python3 scripts/update_benchmarks.py` | 1 条命令 | `BENCHMARKS.md:3-4` | 成立 |
| 12 | 失败模式清单已固定 21 条：11 条标记已修 `[x]`，9 条仍活跃 `[ ]` | 21 = 11 + 9 | `docs/FAIL_PATTERNS.md:3`、`docs/FAIL_PATTERNS.md:435-451` | 成立 |
| 13 | 最大单一失败模式是 noop 支配：v8 里 73/178 条（41.0%）读完遥测就升级、从不尝试修复；最差类别 MEM、NET 各 9/12 | 73/178 = 41.0% | `docs/FAIL_PATTERNS.md:136`、`docs/FAIL_PATTERNS.md:444` | 成立 |
| 14 | 第二大失败模式是升级偏好：v8 里约 155/178 条（87.1%）修好了也不肯说 `everything_ok` | 155/178 = 87.1% | `docs/FAIL_PATTERNS.md:168`、`docs/FAIL_PATTERNS.md:445` | 成立 |
| 15 | 失败模式的优先级由仓内明写：noop 支配 > 假成功 > 升级偏好 > 立即升级 > 部分修复 > 错误假设 > 浅层探查 | 7 项排序 | `docs/FAIL_PATTERNS.md:453-455` | 成立 |
| 16 | 原生路径无第三方 Python 依赖；测试用标准库 unittest 跑，Docker 相关测试在无 Docker 时跳过 | 0 个依赖 | `README.md:22`、`README.md:73-79` | 成立 |
| 17 | 本地模型权重不入库：`.gguf` 被 git 忽略，仓内只留机器本地的符号链接 | 0 个权重文件入库 | `README.md:101-102`、`.gitignore:19` | 成立 |
| 18 | 一台机器上跑全量语料耗时 15–30 分钟（并发 4） | 15–30 min | `README.md:100` | 成立 |
| 19 | 许可证 GPL-3.0 | 1 个许可证 | `README.md:4`、`LICENSE` | 成立 |

## 负结果

| # | 结论 | 关键数字 | 出处 | 状态 |
|---|---|---|---|---|
| N1 | 提示词工程在这批小模型上收益递减，并两次被记录为"改坏了"：v7 回退使 noop 从 77 升到 88；v6 那条规则使 `everything_ok` 从 95 掉到 19、升级从 83 涨到 158 | 95→19、83→158 | `docs/FAIL_PATTERNS.md:150`、`docs/FAIL_PATTERNS.md:192`、`CHANGELOG.md:46-48` | 成立 |
| N2 | v12 的两处改动（few-shot 示例 + "魔法注释"提示）都反效果，已回退；最好提示词停在 v11 的 33.88% | −2.53pp | `CHANGELOG.md:34-50` | 成立 |
| N3 | 逐轮收益接近零：v3 提示词强化 noop 81→81（无变化），v6 加诊断流程 77→77（无变化） | 2 次 0 变化 | `docs/FAIL_PATTERNS.md:147`、`docs/FAIL_PATTERNS.md:149` | 成立 |
| N4 | 没有 CI：仓库徽章直接写 "CI not configured" | 0 个流水线 | `README.md:4` | 成立 |
| N5 | 分数不可跨运行直接比较，依赖模型权重、量化、提示词版本、服务端设置、Docker 镜像与主机资源；单次成功也不证明未建模主机上的安全 | — | `README.md:98-99` | 成立 |
| N6 | 语料规模本身不整齐：多轮只跑 178 条而非 184 条，v8b 只跑 15 条 | 178 vs 184 vs 15 | `BENCHMARKS.md:10-29` | 成立 |
| N7 | 完整论文包、获批视频工件、稳定打包发布三项未做 | 3 项 | `docs/project-status.md:28-32` | 成立 |
| N8 | `README.md:21` 说安全性违规把分数封顶在 0.20，但实现与 changelog 都是 0.25（0.20 是 2026-08-04 之前的旧值） | 0.20 vs 0.25 | `README.md:21` 对照 `harness/bash_sandbox_benchmark.py:474-477`、`CHANGELOG.md:11` | 部分 |
| N9 | 假成功是最贵的一条失败：约 9/22 条已声称 `everything_ok` 的案例是假的，潜在损失约 30 分 | ~9/22、~30 | `docs/FAIL_PATTERNS.md:443` | 成立 |

## 撤回 / 回退记录

| # | 记录 | 关键数字 | 出处 | 状态 |
|---|---|---|---|---|
| R1 | v12 的 few-shot 示例与"魔法注释"提示，两条改动都被回退 | 2 处 | `CHANGELOG.md:34-44`、`CHANGELOG.md:50` | 已撤回 |
| R2 | v7 的 Step 7/8 改动被回退，因为它是回归：noop 77→88（+11） | +11 | `docs/FAIL_PATTERNS.md:150`、`docs/FAIL_PATTERNS.md:193` | 已撤回 |
| R3 | v1 的"先不要调 everything_ok"拦截被记为"made it worse"（模型更谨慎） | — | `docs/FAIL_PATTERNS.md:182-183` | 已撤回 |
| R4 | v6 的"Do NOT call everything_ok if no repair was attempted"被记为回归：`everything_ok` 95→19，升级 83→158 | 95→19、83→158 | `docs/FAIL_PATTERNS.md:192` | 已撤回 |
| R5 | v2 曾整体删掉后台遥测注入器 `_run_injector()`（它污染模型状态） | 1 个函数 | `docs/FAIL_PATTERNS.md:57-67` | 已撤回 |
| R6 | 打分惩罚项 "Scoring penalty" 被标记为 "replaced" | 1 项 | `docs/FAIL_PATTERNS.md:440` | 已撤回 |

## 未知（仓内无法确定，不做推断）

- 当前代码在当下环境能否复跑出 `BENCHMARKS.md` 里的分数：本任务禁止运行，未复跑，未知。
- `docs/FAIL_PATTERNS.md:451` 记 context exhaustion 为 "0 (mitigated)"，缓解手段的实际效果仓内没有测量记录，未知。
- Docker 相关测试的实际通过情况：`README.md:79` 只说"有 Docker 就跑，没有就跳"，本次未运行，未知。
- 184 条场景各自的判定脚本质量、以及有没有场景本身写错：仓内没有审阅记录，未知。
