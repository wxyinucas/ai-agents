# AI Agents｜课程代码与每周练习

本仓库统一保存本课程的代码、Notebook、样例、测试与教师参考。台本、Slides 和学生 Guide 由 [teaching-hub](https://github.com/wxyinucas/teaching-hub) 按学期维护；每周具体要求以课程网站为准。

## 从哪里开始

新取得仓库时，建议使用整门课的名称：

```bash
git clone https://github.com/wxyinucas/ai-agents.git ~/course/ai-agents
cd ~/course/ai-agents
```

已经使用 `~/course/w02-workbench` 的同学继续使用原目录与 Git 历史。它只是 W2 首次 clone 时的本地名称，包含整门课；更新时按 [目录迁移说明](MIGRATION.md) 保留自己的改动。无需再次 clone 或修改目录名。

进入当周目录后，再恢复该目录自己的环境并执行命令。仓库根目录只承担导航；W2 的程序和 uv 配置现已归入 `week-02/`。

| 入口 | 内容与操作说明 |
| --- | --- |
| [week-02/](week-02/) | 命令行、项目环境与本地 Git；[Course Check](week-02/README.md) |
| [week-03/](week-03/) | Agent、蒲丰投针实验与 LaTeX 报告；[使用说明](week-03/README-materials.md) |
| [week-04/](week-04/) | 配置隔离、Notebook、故障对照与公开测试；[使用说明](week-04/README-materials.md) |
| [week-05/](week-05/) | 容器操作、遍历、函数任务与 CI；[使用说明](week-05/README-materials.md) |
| [week-06/](week-06/) | 函数、调用与可见性的六个纠错场景；[使用说明](week-06/README.md) |
| [week-07/](week-07/) | NumPy 数值计算调试、教师演示与练习；[使用说明](week-07/README.md) |
| [week-08/](week-08/) | 项目维护、R／MATLAB 工作台与 PostgreSQL 演示；[使用说明](week-08/README.md) |
| [week-09/](week-09/) | Longbridge 数据批次、校验、离线分析与教师成品；[使用说明](week-09/README.md) |
| [demos/](demos/) | 可独立运行的教师展示，例如 [W3 动态投针演示](demos/week-03-buffon/README.md) |
| [project/](project/) | 后续持续演化的项目；启用方式随相应周次明确 |
| [legacy/market-lab/](legacy/market-lab/) | 从旧项目仓库整理的历史行情实验与参考素材，供按需选用 |

## 周材料与持续项目

- `week-XX/` 保存当周任务、练习、样例、测试与参考；需要 Python 环境的周次使用各自的 `pyproject.toml`、`uv.lock` 和 `.venv/`。
- `project/` 承载后续持续维护的一份项目代码；具体开始时间与结构由当周任务确定。
- `legacy/` 的旧周号不等于当前课程周号。历史材料不构成补做要求，也不自动成为持续项目的基线。

学生继续保留当前仓库与个人提交。教师材料的 remote 可能叫 `origin` 或 `upstream`，更新前用 `git remote -v` 确认；不按周重复 clone，也不在周目录中另行 `git init`。
