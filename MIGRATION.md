# 更新已有课程仓库

课程代码统一维护在 `ai-agents`。原来叫 `w02-workbench` 的本地目录仍可继续使用；目录名称不决定仓库内容或课程周次。

本次把原来放在仓库根目录的 W2 内容移到 `week-02/`。已有 `week-03/`～`week-09/` 路径保持；`project/` 留给后续持续项目，`legacy/market-lab/` 保存选取的旧实验素材。

## 先保存自己的工作，再更新

在已有课程仓库根目录执行：

```bash
git status -sb
git remote -v
```

先保存未提交的修改，再确认哪个 remote 指向教师的 `wxyinucas/ai-agents`。根据自己的设置只选一条：

```bash
# 教师仓库叫 origin
git pull --no-rebase origin main
```

```bash
# 已有个人 origin，教师仓库叫 upstream
git pull --no-rebase upstream main
```

已有 commit 会保留在合并历史中。Git 通常能识别文件移动，把已经提交的签名修改跟随到 `week-02/signature.toml`；更新后打开该文件，确认仍是自己的值。

如果报告冲突，保留当前状态，让 Agent 先解释冲突。对签名的目标很简单：本人签名保留在 `week-02/signature.toml`，其他已有成果和提交继续保留。不要把教师默认值当作必须覆盖的“标准答案”。

可以把下面的文字和自己的 `git status -sb`、`git remote -v` 结果交给 Agent：

```text
我要更新已有的 AI Agents 课程仓库。本次上游把根目录 W2 文件移动到 week-02/，
week-03/ 至 week-09/ 路径不变。我已有自己的提交或修改。
请先解释当前状态和教师 remote，再帮助我保存工作并合并更新。
保留本人签名到 week-02/signature.toml，保留其他已有成果与历史，
解决冲突后让我核对实际 diff；不要重新 clone 或抛弃已有提交。
```

## 进入当周目录运行

W2 现在从仓库根进入：

```bash
cd week-02
uv sync --locked
COURSE_MODE=fixture uv run --locked python course_check.py
COURSE_MODE=fixture uv run --locked pytest -q
```

本周 `.venv/` 由 `uv sync` 在新位置建立。旧根目录的虚拟环境与缓存属于本机生成物，不需要复制到新目录。

其他周继续进入自己的 `week-XX/`。W9 教师演示入口仍为 `week-09/reference/`，具体准备见 [W9 README](week-09/README.md)。
