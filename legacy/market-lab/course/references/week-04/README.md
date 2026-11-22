# 旧 W4 trace 任务参考实现

这是在旧 CSV 参考上增加可选 `--trace` 的一种实现，现作为历史素材；它不是当前 W4 任务。它只读取本地 CSV，不访问平台、账户或网络。默认命令维持旧 W3 行为；打开追踪时只向 `stderr` 增加两处诊断线索。迁移来源见 [素材说明](../../../README.md)。

从 `ai-agents/legacy/market-lab/course/references/week-04/` 运行：

```bash
uv sync --locked
uv run --locked pytest -q ../../week-03/tests ../../week-04/tests
uv run --locked market-check ../../week-03/tests/fixtures/another_valid_prices.csv
uv run --locked market-check ../../week-03/tests/fixtures/another_valid_prices.csv --trace
uv run --locked market-check ../../week-03/tests/fixtures/missing_close.csv --trace
```

最后一条命令应明确失败，同时留下两处 trace。本目录用于对照代码行为与公开测试，不承担当前学生作业的初始化或提交。
