# 旧行情实验与 Longbridge 试点（历史素材）

2026-11-22 从 [`wxyinucas/ai-agents-project`](https://github.com/wxyinucas/ai-agents-project) 整理迁入，源快照为 `c8d6f6585712842f824d7f103b28c20c62d86c3c`。原仓库保留 Git 历史和源文件，此处只整理可复用的代码、测试、合成数据与试跑笔记。

**这些材料不是当前 W3／W4 的任务，也不是 `project/` 的起始基线。** 当前课堂从仓库根 README 指定的 `week-XX/` 进入。这里出现的周次、数据合同和平台查询均属于旧方案，不自动变成当前课程要求。

## 材料地图

```text
market-lab/
├── common/                         # 旧数据合同与稳定摘要实现
└── course/
    ├── week-03/                    # 本地 CSV 检查的旧任务、样例与公开测试
    ├── week-04/                    # 增加 --trace 的旧任务与回归测试
    ├── references/week-03/         # 可运行的 CSV 检查参考
    ├── references/week-04/         # 可运行的 trace 参考
    └── pilots/
        ├── longbridge-readonly-v1/ # 静态数据合同、合成输入与测试案例
        └── longbridge-gate-a/      # 历史联网工具、隔离单测与试跑笔记
```

保留 `common/` 与 `course/` 的相对关系，使两份 CSV 参考实现仍能找到原来的公开测试与样例。旧 `students/` 布局不作为本仓库当前结构导入。

## 可直接运行：本地 CSV 与 trace 参考

先进入本仓库的 `legacy/market-lab/`，再选择一份参考。它们只读教学 CSV，不调用券商或读取凭据：

```bash
cd course/references/week-03
uv sync --locked
uv run --locked pytest -q ../../week-03/tests
uv run --locked market-check ../../week-03/data/sample_prices.csv
```

旧 W4 参考在另一独立环境中保留 W3 行为，并增加 `--trace`：

```bash
cd ../week-04
uv sync --locked
uv run --locked pytest -q ../../week-03/tests ../../week-04/tests
uv run --locked market-check ../../week-03/tests/fixtures/another_valid_prices.csv --trace
```

首次恢复环境使用 `uv sync --locked`，可能需要下载依赖。此次 `uv sync --locked --offline` 因本机缺少 `pandas==2.3.3` 的 wheel 缓存未完成；保留原锁文件，首次有网时再恢复即可。迁移行为验证复用了源仓库已安装的同版本依赖，并确认 Python 与 `market-check` 子进程加载的是本目录的新位置源码：旧 W3 的 5 项、旧 W4 的 8 项公开测试通过。没有联网调用或复制旧环境；运行中生成的 `.venv/` 与缓存不进入 Git。

## 静态素材：数据合同与平台试点

- `common/src/course_common/week04.py` 保存旧 `course.market-bars.v1` 合同：来源组合、时区、交易日覆盖、OHLC、有限数值与稳定数据摘要。
- `course/pilots/longbridge-readonly-v1/` 保存配套合成 JSON、故障案例、旧任务与报告模板。它不包含完整可运行的 `market-observe` 项目，不承诺整套测试可以直接执行。
- `course/pilots/longbridge-gate-a/PILOT.md` 保存脱敏的历史试跑记录，不代表当前账号、额度、SDK 或学生 WSL 路线已经重新验证。
- `longbridge-gate-a/main.py` 是会读取并清空剪贴板、调用行情网络接口的历史工具。它没有接入当前教学流程；迁移与本地验收只运行 mock 单测，不执行该程序入口，也不重新授权。

要查看后者的隔离单测，可从其目录运行：

```bash
python3 -m unittest discover -s tests -v
```

## 本次未导入的内容

- `.venv/`、缓存、生成产物和旧学生目录。
- 旧 `course/week-03/init-student.sh`、`course/week-04/init-week.sh`：它们建立旧 `students/sXX/system/`，参考实现与公开测试均不依赖这些脚本。
- `longbridge-readonly-v1/init-week.sh`、`tests/test_w3_regression.py`：已不适配试点目录的相对路径，保留在源仓库历史中，不带入当前入口。

CSV／JSON 样例是教学合成输入；`sensitive-field.json` 中的 `W4_PRIVATE_MARKER_2E4C` 是故障测试标记，不是凭据。真实行情、账户响应、授权码或 token 不在本目录中保存。
