# 旧行情任务的教师参考

这两份参考分别演示本地 CSV 检查，以及增加可选 `--trace` 后如何保持原行为。它们在独立 uv 环境中运行，使用相邻 `course/week-03/`、`course/week-04/` 的公开测试和合成样例。

- [`week-03/`](week-03/)：`market-check <CSV>`。
- [`week-04/`](week-04/)：保留原命令，增加 `market-check <CSV> --trace`。

统一启动方式与迁移来源见 [历史素材说明](../../README.md)。当前 W3 的蒲丰投针、W4 的配置隔离等任务仍从仓库根的 `week-XX/` 进入；这些旧参考不作为 `project/` 的恢复基线。
