# auto_maintain_bench 状态

一句话：一个确定性基准，测小而弱的语言模型能否只用 bash 在隔离 Docker 沙箱里诊断并修复 Linux 主机问题，按可观察结果打分而不是让另一个模型来裁判（`README.md` 标题区、`docs/project-status.md`）。

## 当前状态

**已关闭（里程碑，2026-09-29），不再开发。**

- 关闭声明：`README.md` 顶部状态段与 `docs/project-status.md` 的 Status 一节 —— 后续工作可能转移到 Help Agent，后者可能取代本基准。
- 分类：`docs/project-status.md` 的 Classification 一节 —— 研究原型（已关闭里程碑），从来不是生产级自动修复服务。
- 语料与打分：`docs/project-status.md` 的 Evidence 一节 —— 172 条场景 / 18 个类别；打分覆盖 fix、durability、safety、terminal，不使用 LLM 裁判。
- 交付状态：`docs/project-status.md` 的 Deferred 一节把完整论文包、获批的视频工件、稳定打包版本列为**未做**（版本号如 `v12` 是优化轮次，不是发布版本）。
- 收口提交 2026-09-29（`b94c66a Close out: milestone status; point future work at Help Agent`）；最后一条带分数的版本记录是 v12（`CHANGELOG.md` 的打分规则更新一节，2026-08-04）。
- 边界：本文件只读仓内文件，未运行基准、未跑测试；因此"172 条场景可跑通"未复跑。

## 最新进展落在哪个文件

- 状态与边界：`docs/project-status.md`（分类/状态/证据/版本与可复现/未做）。
- 各版本分数总表与分类明细：`BENCHMARKS.md`（开头写明由 `trajectories/` 自动生成，`python3 scripts/update_benchmarks.py` 重算）。
- 每轮改了什么、分数如何变化：`CHANGELOG.md`（按 v1…v12 分节，顶部是 2026-08-04 的打分规则改动）。
- 失败模式清单（按场景 ID 追踪、`[x]` 已修 / `[ ]` 仍在）：`docs/FAIL_PATTERNS.md`。
- 术语与生产守护进程语境：`CONTEXT.md`。

## 下一步

按仓内原文，没有开发计划；被点名的延续方向只有两条：

- 后续工作可能转移到 Help Agent（`README.md` 顶部状态段、`docs/project-status.md` 的 Status 一节），"may supersede this benchmark"。
- 若要恢复，`docs/project-status.md` 的 Version and reproducibility 一节要求每次可比运行都记录 model、prompt、temperature、concurrency、Docker image、host 资源与 commit；版本标签只是优化轮次（`README.md` 的 Roadmap 一节）。

未完成项（对应 `docs/project-status.md` 的 Deferred 一节）：完整论文包、获批的视频工件、稳定打包发布。
