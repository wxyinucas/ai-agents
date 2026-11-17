# W9｜市场数据批次与离线分析

本目录提供合成样例、独立公开测试与教师参考。学生在自己的 `~/course/w09-market-data/` 中与 Agent 开发，不把参考代码作为起始项目。注册、授权和五个操作单元以课程网站的 W9 Guide 为准。

## 材料分工

```text
week-09/
├── fixtures/                    # 六份合成输入，不是真实行情
├── checks/test_market_data.py   # 复制到学生项目 tests/ 的公开测试
├── reference/
│   ├── checks.py                # validate_bars：检查并返回新列表
│   ├── fetch_batch.py           # 官方 CLI 取数／--input 离线批次
│   ├── analyze.py               # 本地 CSV → 表、图、分析元数据
│   └── tests/                  # 参考实现自身的离线测试
├── pyproject.toml
└── uv.lock                     # 仅用于教师参考的运行环境
```

| 文件 | 预期 |
| --- | --- |
| `good.json` | 完整的三行数据，通过 |
| `unordered.json` | 同样三行乱序，返回新列表并排序，输入保持 |
| `missing-close.json` | 第二行缺少收盘价，拒绝 |
| `duplicate-time.json` | 出现同一时刻，拒绝 |
| `nan-close.json` | 收盘价是字符串 `NaN`，拒绝 |
| `error.json` | 整体是 API 错误对象，不是行情列表，拒绝 |

## 学生获取与分阶段检查

先在已经 clone 的课程仓库中取得教师更新。remote 的名称沿用自己的设置；已有修改先查看 `git status`，遇到 merge 问题可让 Agent 解释和协助，不删除自己的提交。

下面假设课程仓库仍位于 `~/course/w02-workbench`，自己的 W9 项目已按 Guide 初始化。若实际路径不同，只替换材料来源：

```bash
cd ~/course/w09-market-data
mkdir -p fixtures tests
cp ~/course/w02-workbench/week-09/fixtures/*.json fixtures/
cp ~/course/w02-workbench/week-09/checks/test_market_data.py tests/
```

完成 `checks.py` 和 `fetch_batch.py` 后，单元 3 只运行这一组；此时不要求已有 `analyze.py`：

```bash
uv run pytest -q tests/test_market_data.py -k 'validate or fetch'
```

完成单元 4 的分析与 `--tail` 后，再运行全套：

```bash
uv run pytest -q tests/test_market_data.py
```

测试使用自带的合成输入和临时项目副本，检查公开的 `validate_bars(rows)` 与两个命令行入口；不会调用真实 Longbridge。实际 API 接入、授权范围、图的含义与最终清理仍按 Guide 亲自核对。

## 教师参考：先跑离线链路

在课程仓库的 `week-09/` 中：

```bash
uv sync --locked
cd reference
uv run --project .. --locked python fetch_batch.py --batch fixture-demo --input ../fixtures/good.json
uv run --project .. --locked python analyze.py --batch fixture-demo
uv run --project .. --locked python analyze.py --batch fixture-demo --tail 2
```

产物位于当前 `reference/` 的 `data/fixture-demo/` 和 `outputs/fixture-demo/`，均不进入 Git。再次使用同名批次会被拒绝；重做演示时使用新的批次名，并相应修改分析命令。

- 全量 `analysis.csv`：收盘价 `100,110,99`，变化率依次为空、`0.10`、`-0.10`。
- `tail-2/analysis.csv`：保留 `110/0.10`、`99/-0.10`；先在全量数据上计算，再截取两行。
- `figure.png`：上图收盘价，下图百分比变化，共用 UTC 日期轴。
- `source=fixture` 的元数据记录输入文件与本地处理时间，不填写虚构请求或 API 获取时间。

线上入口只在本人完成本周 Basic data 授权后使用：

```bash
uv run --project .. --locked python fetch_batch.py --batch aapl-day-001 --count 100
```

它调用官方 `longbridge kline`，固定 `AAPL.US/day/none/intraday`，仅为子进程指定 `LONGBRIDGE_REGION=global`；登录由 CLI 处理，参考代码不读取凭据。返回多少行就记录多少，不把请求条数当实际条数。此封装已用假 CLI 验证参数、错误处理和来源记录；真实授权与平台返回仍需教师课前实测。

## 验证参考实现

回到 `week-09/`：

```bash
uv run --locked pytest -q
W9_PROJECT_ROOT="$PWD/reference" uv run --locked pytest -q checks/test_market_data.py
```

第一条验证参考实现的 CLI 封装与 CSV 分析；第二条用独立公开契约检查参考实现。两者均为离线测试。首次绘图可能需要建立 Matplotlib 字体缓存。

真实响应、生成图表、账号信息与凭据不放入公开仓库；本目录只保留明确标注的合成输入与代码。
