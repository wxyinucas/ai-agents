# 历史数据合同实现

这里保存旧行情项目的公共实现，迁移来源与使用边界见 [历史素材说明](../README.md)。当前周次的代码与未来 `project/` 不依赖它。

- `course_common.week04.observe_market_file()` 读取本地课程行情 JSON。
- 检查 `course.market-bars.v1`，按时间排序并生成脱敏证据。
- 计算与运行模式无关的稳定 `data_sha256`。

旧任务曾通过 uv 本地 path dependency 使用本包；该接入方式仅作历史记录。这里没有 Longbridge SDK、网络请求或凭证处理。
