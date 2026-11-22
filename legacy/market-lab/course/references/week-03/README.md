# 旧 W3 行情任务参考实现

这是旧本地 CSV 任务的一种实现，只作为历史素材；它不是当前 W3 报告，也不是新持续项目的起点。迁移来源见 [素材说明](../../../README.md)。

从 `ai-agents/legacy/market-lab/course/references/week-03/` 运行：

```bash
uv sync --locked
uv run --locked pytest -q ../../week-03/tests
uv run --locked market-check ../../week-03/data/sample_prices.csv
uv run --locked market-check ../../week-03/tests/fixtures/missing_close.csv
```

最后一条命令应以非 0 退出，说明缺少必要字段。
