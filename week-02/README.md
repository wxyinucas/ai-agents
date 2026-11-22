# W2｜Course Check

这是第二周的独立工作台：观察命令在哪个目录执行、程序使用哪个环境，以及修改如何进入 Git diff 与 commit。完整课堂步骤以课程网站 W2 Guide 为准。

## 打开课程窗口，进入本周目录

新目录示例：

```bash
cd ~/course/ai-agents
code .
```

若一直使用 `~/course/w02-workbench`，第一行使用这个已有仓库路径。旧版根目录内容的更新方法见 [目录迁移说明](../MIGRATION.md)。VS Code 打开课程仓库根目录，便于同时观察 Explorer 与整个仓库的 Source Control。

## 恢复并运行

在该窗口新建 Integrated Terminal，进入本周目录后执行：

```bash
cd week-02
uv sync --locked
COURSE_MODE=fixture uv run --locked python course_check.py
COURSE_MODE=fixture uv run --locked pytest -q
```

本周使用 Python 3.12，程序应显示 `project-env: PASS` 与 `RUNTIME_CHECK=PASS`；Python 的补丁版本按本机实际值记录。初始签名为：

```text
signature: teacher
```

`pyproject.toml`、`uv.lock`、`.python-version`、`signature.toml` 和 `tests/` 均属于本目录。程序报告当前事实，测试检查已经写下的规则；还需按任务核对实际目录、环境与改动。

## 保存自己的公开签名

在 VS Code 中编辑 [`signature.toml`](signature.toml)，例如：

```toml
[student]
signature = "s07"
```

这是示例公开代号，程序不强制此格式。签名不使用姓名、完整学号、密码或 token。

在本周目录核对并提交：

```bash
git status --short
git diff -- signature.toml
git add signature.toml
git commit -m "w2: set public signature"
```

commit 保存到整个课程仓库已有的历史。W2 的练习只要求本地提交，后续发布与 remote 设置按相应周次执行。

W3 的实验位于相邻的 `week-03/`，使用自己的环境；本周不是后续报告或量化项目的代码基线。
