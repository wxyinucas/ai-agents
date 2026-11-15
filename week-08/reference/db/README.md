# 教师准备｜PostgreSQL 取数演示

学生不安装数据库，也不使用教师凭证。`week-08/data/` 已有合成备用文件；它们没有经过数据库查询，来源标记为 `synthetic_fixture`。本目录的准备程序只在教师明确执行时连接服务。

## 1. 准备课程专用连接

需要一个已经可用的 PostgreSQL 服务和能创建课程 schema 的管理员账号。选择自己的课程演示数据库；下面不安装或启动数据库，不修改现有业务表。

在本机项目外配置 `~/.pg_service.conf`，将占位值替换为自己的服务信息。不要将真实配置粘贴给 Agent 或放进投影。

```ini
[w08_demo_admin]
host=YOUR_HOST
port=5432
dbname=YOUR_DEMO_DATABASE
user=YOUR_SETUP_USER

[w08_demo]
host=YOUR_HOST
port=5432
dbname=YOUR_DEMO_DATABASE
user=w08_reader
```

需要密码时，放入本机 `~/.pgpass`，格式为 `host:port:database:user:password`；不要写在命令参数、Notebook 或仓库里。macOS／WSL 用 `chmod 600 ~/.pgpass`。已有这两个配置文件时，在原文件中补充对应条目，不要覆盖原配置。服务端如果要求 TLS，在 service 条目中按实际要求设置。

官方说明：[连接 service 文件](https://www.postgresql.org/docs/current/libpq-pgservice.html)、[密码文件](https://www.postgresql.org/docs/current/libpq-pgpass.html)。这些文件是项目外的本机配置，不表示 Agent 自动失去了读取权限；不要让 Agent 搜索或读取真实凭证。

## 2. 显式建立课程表并装入两批合成记录

从 `week-08/` 开始：

```bash
uv sync --locked --extra database
cd reference
uv run --locked --extra database python db/prepare_db.py --service w08_demo_admin
```

程序创建 `w08_demo.batches`、`w08_demo.measurements`，装入课程自带的校准和应用 CSV。重复执行仅替换这两批课程记录；不清空其他 dataset 或 schema。两批记录在同一事务中更新，任一步失败则回滚。

管理员在自己的 `psql` 中创建课堂只读用户。若已有同名角色，跳过创建并核对权限：

```sql
CREATE ROLE w08_reader LOGIN;
```

然后在 `psql` 使用 `\password w08_reader` 交互设密，不把真实密码写进 SQL 文件。继续授予课程表查询权限：

```sql
GRANT USAGE ON SCHEMA w08_demo TO w08_reader;
GRANT SELECT ON w08_demo.batches, w08_demo.measurements TO w08_reader;
```

将只读账号的密码加入本机密码文件。如果服务器限制数据库连接，还需由管理员按该实例的实际策略授予连接权限。

## 3. 在投影前试跑

仍在 `reference/`：

```bash
uv run --locked --extra database python fetch_data.py --dataset calibration --out data/db-calibration.csv
uv run --locked python analyze.py --input data/db-calibration.csv --prefix outputs/db-calibration
uv run --locked --extra database python fetch_data.py --dataset application --out data/application.csv
```

- 校准 CSV 与 `../data/calibration.csv` 按 `sample_id` 对齐后，应在数值容差内一致。
- 元数据分别保留原生成时间和本次导出时间；只有实际查询产生的输出标记 `source.kind=postgresql`。
- 导出程序不读取表中的 `config`；尤其应用批次的分发元数据不包含真实生成参数或连接信息。
- 课堂账号只有查询权限；客户端也设置只读事务。准备表、写入数据使用独立管理员连接，课堂不运行准备脚本。

如果服务不可用，明确说明使用 `week-08/data/` 的合成副本，继续本地分析；不要修改来源标记伪装成数据库响应。
