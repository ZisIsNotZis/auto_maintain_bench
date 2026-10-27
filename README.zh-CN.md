<p align="center"><img src="assets/logo.svg" width="112" alt="Auto Maintain Bench 标志"></p>
<h1 align="center">Auto Maintain Bench</h1>
<p align="center"><strong>用一套确定性测试，检验小型本地模型能否只靠一个 bash 工具修好 Linux 主机。</strong></p>
<p align="center">172 个沙箱维护场景。每轮一个命令。不让另一个模型当裁判。</p>
<p align="center"><a href="README.md">English</a> · <a href="LICENSE">GPL-3.0</a> · Python 3.10+</p>

> **状态：研究里程碑已收口（2026-09-29）。** harness 和场景库已达到可用的研究状态，不再继续开发；未来可能转入 [Help Agent](https://github.com/ZisIsNotZis/helpagent)，后者可能取代本基准。

## 🚀 快速开始

前置条件：Python **3.10+**、Docker，以及 `llama-server`（或兼容 OpenAI 风格的接口）。仓库不附带模型权重；请提供本地 GGUF 文件，或指向已有的推理服务。

```bash
git clone https://github.com/ZisIsNotZis/auto_maintain_bench.git
cd auto_maintain_bench
python3 benchmark/run.py --model /path/to/model.gguf \
  --scenario CPU-001 --output /tmp/auto-maintain-cpu.json
```

本地运行器会启动 `llama-server`，Docker 沙箱默认使用 `local-os/default:latest`。已有推理服务时：

```bash
python3 benchmark/run.py --model local-model \
  --base-url http://127.0.0.1:8080/v1 \
  --scenario CFG-001 --output /tmp/result.json
```

跑完整语料并把轨迹写到仓库外：

```bash
python3 benchmark/run.py --model ./model.gguf --concurrency 4 \
  --trajectory-dir /tmp/maintain-trajectories --version v1 --output /tmp/all.json
```

## ✅ 现在能做什么

- **在隔离的 Docker 沙箱里运行 18 个类别、172 个项目场景**：CPU、内存、磁盘、网络、配置、进程、安全、产物、服务和用户请求。
- **驱动本地 GGUF 模型**（通过 `llama-server`），或接入任意 OpenAI 兼容接口。
- **执行严格的工具契约**：每轮只发一个 bash 调用，用 `everything_ok` 或 `escalate <level> <message>` 结束，修改前先备份，重复命令直接返回缓存结果。
- **按可观察结果确定性评分**：修复 60%、持久性 20%、安全性 15%、终止行为 5%。没有第二个模型给第一个模型打分。
- **保存逐场景轨迹**，并用 `scripts/update_benchmarks.py` 重新生成基准表。
- **运行生产循环概念验证**：`harness/maintain.py` 用 `MEMORY.md` 作为唯一的跨周期模型记忆。
- **对比已记录的多模型结果**：0.8B–9B 模型见 [BENCHMARKS.md](BENCHMARKS.md)。

### 为什么需要这个基准

小型模型很少被检验能否安全修复真实运维问题。本项目要回答一个具体问题：*一个本地小模型能否诊断主机、做出最小且安全的修改、验证结果，并在不该动手时正确升级？*

- **可复现：** 固定遥测、提示词、随机种子、检查项和场景状态。
- **可观察：** 每一分都来自检查项，而不是主观判断。
- **关注安全：** 出现未预期修改或假的 `everything_ok` 时，最高分被限制在 **0.25**。
- **本地优先：** 原生路径**不需要第三方 Python 依赖**，可以完全跑在本地模型上。
- **贴近运维：** 场景是带运行时证据的真实项目夹具，不是知识问答。

## 🧭 架构

三层结构，一套运行时契约：

| 层 | 路径 | 职责 |
| --- | --- | --- |
| 场景库 | `scenarios/` | 172 个自包含项目：遥测、夹具、修复说明、检查项和评分元数据 |
| Harness | `harness/` | 提示词策略、bash 工具 schema、维护循环、Docker 沙箱、契约、评分、遥测和生产循环守护进程 |
| 基准运行器 | `benchmark/run.py` | 选择场景、调用 harness、写出 JSON 报告和轨迹的 CLI |

配套内容在 `tests/`（标准库检查）、`docs/`（设计、目录、ADR、失败分析、遥测）和 `scripts/`（本地探针与基准辅助脚本）。

每次运行都走同样的五步：

1. 场景提供有限的遥测、项目 README、预期的终止行为、检查项和允许修改的契约。
2. 模型每轮只发一个 bash 工具调用；Docker 在隔离沙箱中执行。
3. harness 校验调用、执行备份和路径规则，并记录结果。
4. 修复、持久性、安全性和终止检查产出分数，并可选写出轨迹 JSON。
5. 运行器把结果汇总成报告，用于跨模型、跨提示词版本比较。

## 🧪 开发方式

原生测试不需要安装依赖：

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

有 Docker 时会运行 Docker 测试，没有时会跳过。手动启动本地推理服务：

```bash
PORT=8091 ./scripts/start_llama_server.sh /path/to/model.gguf
```

贡献规则见 [CONTRIBUTING.md](CONTRIBUTING.md)，设计与基准参考见 [docs/README.md](docs/README.md)。

## 🤝 参与贡献

欢迎贡献确定性场景、明确的校验器、沙箱探针、模型适配器和分析工具。请保持测试不破坏宿主机、避免云端依赖，并说明改动会如何影响分数解释。

请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)、[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 和 [SECURITY.md](SECURITY.md)。项目状态和证据边界记录在 [docs/project-status.md](docs/project-status.md)。

## 🛣️ 路线图

### 已实现

- 18 个类别、172 个项目的确定性场景库，覆盖修复、回归和持久性检查。
- Docker 隔离的 bash agent 循环，带修改前备份、重复命令检测和终止命令校验。
- 不依赖 LLM 裁判的确定性评分，并对未预期修改和假成功设置安全上限。
- 本地 GGUF 与远程 OpenAI 兼容传输、轨迹保存和基准表生成。
- 带周期遥测和 `MEMORY.md` 连续性的生产循环概念验证。
- 0.8B、2B、4B、9B 模型的已记录对比，见 [BENCHMARKS.md](BENCHMARKS.md)。

### 计划中（未排期——项目已收口）

- 在保持场景和评分契约稳定的前提下，补充高价值边界案例。
- 改进本地模型和已有推理服务的适配器。
- 发布更清晰的跨模型报告和失败复现流程。
- 在接入守护进程前，先满足沙箱、审批、回滚、遥测完整性和持久验证要求。

**未来形态：** 它可以成为边缘维护守护进程的可信评测与回归套件，而不是自动运行的 root shell。真正的价值是提供一种可重复的方法：发现小模型从哪一步开始不再安全，并证明一次改动究竟有没有让它变好。

## ⚠️ 注意事项

- 结果受模型权重、量化方式、提示词版本、服务参数、Docker 镜像和主机资源影响。
- 场景得分成功不代表对未建模主机也安全。
- 并发数为 4 时完整运行可能需要 **15–30 分钟**，并消耗较多资源。
- 模型文件属于本机，不是可移植的仓库资源。
- `scripts/` 含有工作站特定模型路径，使用前请调整。
- `v12` 等基准标签表示优化轮次，不代表兼容性保证。每次结果都应保存模型、提示词、运行时环境和提交信息。

## 📜 许可证

本项目采用 [GNU GPL v3.0](LICENSE) 授权。
