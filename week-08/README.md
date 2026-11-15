# W8｜从新项目到数据分析

本周三个教学点：项目与需求变更 → R／MATLAB 工作台 → PostgreSQL 与外部数据。

**学生在自己的 VS Code 中与 Agent 开发；`demo.ipynb` 是教师的展示与讲解平台。** 学生不必安装 Jupyter 或数据库。

## 学生从哪里开始

继续更新已有的课程仓库，从中取得公开测试与应用数据；另建 `~/course/w08-analysis` 完成自己的项目。

- 第一轮：按短 Prompt 完成模拟和一元回归分析。
- 第二轮：新增 `noise-002`、`seed-003`，保留 `base-001` 的数据和结果。
- 第三轮：对照工程设计，理解配置、批次命名与元数据，再按需要调整自己的项目。

完整操作见 [W8 Guide](https://wxyinucas.github.io/teaching-hub/#/terms/2026-fall/courses/ai-agents/weeks/week-08/guide)。第一轮不要求照抄参考布局，后续按课堂进展查看。

| 材料 | 职责 |
| --- | --- |
| `checks/test_analysis.py` | 复制到学生项目 `tests/`，检查自己的 `analyze.py` 中的 `fit_line(x,y)`。 |
| `demo.ipynb` | 教师展示三轮需求、工程设计、分析与外部取数。 |
| `reference/` | 最终参考项目，包含 Python 分析、R 绘图和只供导读的 MATLAB 代码。 |
| `reference/configs/` | 实验设计与批次配置。 |
| `data/` | 小规模合成备用记录和同名元数据；不声称来自本次数据库调用。 |
| `reference/db/` | 教师准备数据库的步骤与课程表结构。 |
| `pyproject.toml`、`uv.lock` | 教师 Notebook 与参考项目的 Python 环境。学生新项目使用自己的环境。 |

公开测试在学生项目根目录执行：

```bash
uv run pytest -q
```

也可从本周目录检查参考实现：

```bash
W8_PROJECT=reference uv run --locked pytest checks/test_analysis.py -q
```

## 教师：打开演示 Notebook

在已更新的 `week-08/` 中运行：

```bash
uv sync --locked --extra database
uv run --locked --extra database python -m ipykernel install --sys-prefix --name ai-agents-week-08 --display-name "W8 Python 3.12"
uv run --locked --extra database jupyter notebook demo.ipynb
```

使用此次终端给出的完整本机链接，保留其中的 token；Notebook 选择 **W8 Python 3.12**。VS Code 中也可选择本目录 `.venv` 的 Python 打开。

教师启动流程保留 `--extra database`，使 Notebook 中的 Python 已具备数据库客户端。它不会安装数据库服务器，也不会自动连接；现场取数仍由 `RUN_DATABASE` 开关控制。单独运行不带 extra 的 `uv sync --locked` 会移除这项可选依赖，之后需按上面的流程重新同步。

发布的 Notebook 不含运行输出。教师按顺序执行，演示产物写入 `.generated/`；课堂前重启 kernel。覆盖文件的对照只作用于临时副本，不覆盖公布的材料。

Notebook 的 R 演示需要系统中的 `Rscript`；缺少时明确提示并跳过，不生成伪造结果。MATLAB 示例只展示代码，不执行。R／MATLAB 扩展配置见 Guide，授课前在实际演示机检查。

## 教师：运行参考项目

在本周目录完成上面的环境准备后：

```bash
cd reference
uv run --locked python simulate.py --config configs/base-001.json --out data/base-001.csv
uv run --locked python analyze.py --input data/base-001.csv --prefix outputs/base-001
Rscript plot.R data/base-001.csv outputs/base-001-r.png
```

将配置换成 `configs/noise-002.json`、`configs/seed-003.json`，同时更换数据与输出文件名，即可比较后续批次。每批 CSV 旁保留同名 `.meta.json`，图和系数对应同一输入。

Python 环境由 `uv` 管理；R 使用系统中的 R；二者通过 CSV 交接，不互相调用。`analysis.m` 保持未执行状态。

## 教师：PostgreSQL 现场演示

先按 [数据库准备说明](reference/db/README.md) 在自己的环境配置课程表与只读连接，再安装可选客户端依赖：

```bash
uv sync --locked --extra database
cd reference
uv run --locked --extra database python fetch_data.py --dataset calibration --out data/db-calibration.csv
uv run --locked --extra database python fetch_data.py --dataset application --out data/application.csv
```

实际连接信息由教师在仓库外配置，不放进 Notebook 或 Agent 对话。Notebook 默认使用合成备用记录；确认环境准备完成后，才将数据库执行开关设为开启。只有这次请求成功取得的结果才描述为现场数据库调用。

连接不可用时，用 `data/` 中的合成 CSV 与元数据继续分析，并说明来源；这不等于完成数据库连接。学生只领取 CSV 和元数据，不需要数据库账号。
