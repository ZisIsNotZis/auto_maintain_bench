# auto_maintain_bench 状态

一句话：一个确定性基准，测小而弱的语言模型能否只用 bash 在隔离 Docker 沙箱里诊断并修复 Linux 主机问题，按可观察结果打分而不是让另一个模型来裁判（`README.md:3`、`README.md:13-15`）。

## 当前状态

**已关闭（里程碑，2026-09-29），不再开发。**

- 关闭声明：`README.md:6-9` —— "Status: closed (milestone, 2026-09-29)"，后续工作可能转移到 Help Agent，后者可能取代本基准。
- 分类：`docs/project-status.md:5` —— 研究原型（已关闭里程碑），从来不是生产级自动修复服务。
- 语料与打分：`docs/project-status.md:16-18` —— 184 条场景 / 19 个类别；打分覆盖 fix、durability、safety、terminal，不使用 LLM 裁判。
- 交付状态：`docs/project-status.md:28-32` 把完整论文包、获批的视频工件、稳定打包版本列为**未做**（版本号如 `v12` 是优化轮次，不是发布版本）。
- 仓库最后一次提交 2026-10-15（`bfac561 Stop tracking machine-local model symlinks and document model setup`）；最后一条带分数的版本记录是 v12（2026-08-04）。
- 边界：本次只读仓内文件，未运行基准、未跑测试；因此"184 条场景可跑通"未在本次复跑。

## 最新进展落在哪个文件

- 状态与边界：`docs/project-status.md`（分类/状态/证据/版本与可复现/未做）。
- 各版本分数总表与分类明细：`BENCHMARKS.md`（`BENCHMARKS.md:3` 写明由 `trajectories/` 自动生成，`python3 scripts/update_benchmarks.py` 重算）。
- 每轮改了什么、分数如何变化：`CHANGELOG.md`（按 v1…v12 分节，当前顶部是 2026-08-04 的打分规则改动）。
- 失败模式清单（按场景 ID 追踪、`[x]` 已修 / `[ ]` 仍在）：`docs/FAIL_PATTERNS.md`。
- 术语与生产守护进程语境：`CONTEXT.md`。

## 下一步

按仓内原文，没有开发计划；被点名的延续方向只有两条：

- 后续工作可能转移到 Help Agent（`README.md:6-9`、`docs/project-status.md:10-12`），"may supersede this benchmark"。
- 若要恢复，`docs/project-status.md:26` 要求每次可比运行都记录 model、prompt、temperature、concurrency、Docker image、host 资源与 commit；版本标签只是优化轮次（`README.md:112`）。

未完成项（原样照搬 `docs/project-status.md:28-32`）：完整论文包、获批的视频工件、稳定打包发布。
