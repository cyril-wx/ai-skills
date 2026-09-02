---
name: multi-agent-copaw
description: "CoPaw 2.0 多智能体协作技能 — 搭建、配置和管理多智能体协作系统：创建智能体、启用 multi_agent_collaboration 协作技能、智能体间对话、后台任务、spawn_subagent 子任务、结果汇总。触发词：多智能体、多智能体协作、智能体团队、agent 协作、多个智能体、让别的智能体、CoPaw 多智能体、multi-agent collaboration、智能体互聊。"
metadata:
  {
    "builtin_skill_version": "2.1.1",
    "copaw":
      {
        "emoji": "🤝",
        "requires": {"bins": [], "envs": []}
      }
  }
---

# CoPaw 多智能体协作技能

> 适用于 **CoPaw 2.0**（CLI 为 `qwenpaw`，工作目录默认 `~/.qwenpaw`）。
> 若当前环境仍是 1.0（`copaw` CLI / `~/.copaw` 目录），本技能**不适用**，先按「Step 0」引导用户升级。

## TL;DR

1. **先探测环境**：`qwenpaw --version` 确认是 2.0
2. **建 3-5 个智能体**为宜，各专注一个领域；**description 字段是协作路由的关键**，必须写清专长
3. **推荐在 Console 创建智能体**（Settings → Agent Management）；手动操作时只写 `agent.json` + `AGENTS.md`/`SOUL.md`，**PROFILE.md 由系统自动生成，不要手写**
4. 让各智能体在 Console（Workspace → Skills）或 `qwenpaw skills config` 中**启用 `multi_agent_collaboration` 技能**，之后它们才能互相协作
5. 配置改动**约 2 秒热加载，无需重启**
6. 跨智能体协作用 `chat_with_agent`（CLI：`qwenpaw agents chat`）；当前项目内的子任务用 `spawn_subagent`

## Step 0: 环境发现与版本检查（必做）

```bash
qwenpaw --version          # 应为 2.0+
echo $QWENPAW_WORKING_DIR  # 默认 ~/.qwenpaw
qwenpaw agents list        # 列出已有智能体（ID/名称/description/工作区/Profile）
```

| 探测结果 | 处理 |
|---------|------|
| `qwenpaw` 未找到，但存在 `copaw`（1.0） | 告知用户本技能仅支持 2.0 → 引导：备份工作目录（`cp -r ~/.copaw ~/.copaw.backup`）并升级 CoPaw 至最新版后重跑本流程 |
| 两个 CLI 都不存在 | 引导安装 CoPaw 2.0 并运行 `qwenpaw init` 初始化 |
| `qwenpaw agents list` 报服务未启动 | 先启动服务（`qwenpaw app`），再重试 |
| 工作目录不是默认值 | 以 `$QWENPAW_WORKING_DIR` 为准，后续所有路径替换前缀 |

## Step 1: 规划团队（⚠️ 检查点：先与用户确认）

向用户确认智能体清单：ID、名称、description（专长 + 技能范围 + 擅长任务类型）。

- 数量建议 **3-5 个**，按主要职能或平台划分；不要为每个小功能建智能体
- ID 命名要清晰：`work-assistant`、`code-reviewer` ✅；`test1`、无意义随机串 ❌
- description 示例：
  - ✅ "专精 Python/JavaScript 代码审查、重构与性能优化"
  - ❌ "我的助手" / "用于测试" / 留空
- 全局共享：模型 provider（API key、模型选择）、环境变量；独立配置：渠道、技能、会话历史、cron 任务、persona 文件

**将规划表展示给用户，确认后再执行 Step 2。**

## Step 2: 创建智能体

### 方式 A: Console（推荐）

1. **Settings → Agent Management** → Create Agent
2. 填写 Name、Description（**必填且要写清专长**）、ID（留空则自动生成，或自定义如 `coder`）
3. 创建后左上角 Agent Selector 即可切换；再逐一切换配置：
   - Control → Channels（渠道）
   - Workspace → Skills（技能开关）
   - Workspace → Tools（内置工具）
   - Workspace → Files（编辑 AGENTS.md / SOUL.md）

### 方式 B: 文件/API（批量创建）

```bash
WORKSPACE_ROOT="${QWENPAW_WORKING_DIR:-~/.qwenpaw}/workspaces"
mkdir -p "$WORKSPACE_ROOT/researcher"
```

1. 在每个智能体工作区写 `agent.json`（核心字段）：

```json
{
  "id": "researcher",
  "name": "研究员",
  "description": "负责信息搜集、多源验证与研究分析",
  "workspace_dir": "",
  "language": "zh",
  "system_prompt_files": ["AGENTS.md", "SOUL.md", "PROFILE.md"]
}
```

2. 为每个智能体写 `AGENTS.md`（角色职责）与 `SOUL.md`（行为原则），模板见 `TEMPLATES.md`。**不要手写 PROFILE.md**——系统基于 name/description/技能/persona 自动生成于工作区根目录
3. 在全局 `config.json` 注册 profile（保留已有字段，只增补 `agents.profiles`）：

```json
{
  "agents": {
    "active_agent": "default",
    "profiles": {
      "researcher": {
        "id": "researcher",
        "name": "研究员",
        "description": "负责信息搜集、多源验证与研究分析",
        "enabled": true
      }
    }
  }
}
```

4. 或用 REST API 创建：`curl -X POST http://<host>:<port>/api/agents -H "Content-Type: application/json" -d '{"name": "...", "description": "..."}'`（host/port 见「REST API」节）

> `workspace_dir` 可省略，默认 `$QWENPAW_WORKING_DIR/workspaces/{id}`。chats.json、jobs.json、PROFILE.md 等运行时文件由系统自动维护。

### 方式 C: 自动化脚本（批量团队）

```bash
# 预设团队：content / dev / research
python3 <skill_dir>/multi_agent_setup.py --team content
# 单个智能体
python3 <skill_dir>/multi_agent_setup.py --name "协调者" --role coordinator --id coordinator
# 批量配置文件
python3 <skill_dir>/multi_agent_setup.py --batch agents_config.json
```

## Step 3: 启用协作技能（多智能体互聊的前提）

```bash
# 交互方式（CLI 唯一方式）：找到 multi_agent_collaboration，空格切换，回车保存
qwenpaw skills config --agent-id <agent_id>

# 查询启用状态（✓ enabled 行）
qwenpaw skills list --agent-id <agent_id>
```

> ⚠️ `qwenpaw skills enable` 命令**不存在**，不要使用；`skills list` 也没有 `--status` 参数。
> 需要非交互/脚本化启用时：直接编辑目标智能体工作区的 `skill.json`，为 `multi_agent_collaboration` 增加/修改 `{"enabled": true}` 条目，约 2 秒热加载生效。

Console 方式：切换到该智能体 → Workspace → Skills → 勾选 **Multi-Agent Collaboration** → Save。

**参与协作的每个智能体都要启用**，否则只能"被调用"或无法发起协作。

## Step 4: 验证与测试（⚠️ 测试通过后才交付）

```bash
# 1. 确认智能体已加载（新增智能体靠热加载生效，无需重启）
qwenpaw agents list

# 2. 测试跨智能体对话
qwenpaw agents chat \
  --from-agent default \
  --to-agent researcher \
  --text "请研究人工智能的最新发展"
```

- 新智能体未出现在列表中 → 先执行 `qwenpaw daemon reload-config`（重读配置文件）；仍无效则按 `qwenpaw daemon restart` 打印的指引重启服务进程（该命令本身不重启进程）
- 对话无响应 → 检查该智能体是否启用了协作技能、`description` 是否为空、日志（`qwenpaw daemon logs`）

## 智能体间通信（chat_with_agent）

```bash
# 1) 新建会话（实时模式，适合快速查询）
qwenpaw agents chat --from-agent <current> --to-agent <target> --text "请求内容"

# 2) 多轮会话（维持上下文）
qwenpaw agents chat --from-agent <current> --to-agent <target> \
  --session-id "<session_id>" --text "后续请求"

# 3) 复杂任务（后台模式：数据分析、批量处理、报告生成等）
qwenpaw agents chat --background --from-agent <current> --to-agent <target> --text "复杂任务"
# → 返回 [TASK_ID: xxx] [SESSION: xxx]

# 4) 轮询后台任务状态
qwenpaw agents chat --background --task-id <task_id>
# 状态流: submitted → pending → running → finished（completed ✅ / failed ❌）
```

模式选择：

| 场景 | 模式 |
|------|------|
| 快速查询、简短请求 | 实时（1） |
| 同一任务的追问 | `--session-id` 续聊（2） |
| 耗时/执行时间不确定的任务 | `--background` + 轮询（3/4） |

> 日常使用中这些命令由启用协作技能的智能体在后台自动执行，用户通常直接对当前智能体说话即可（如"请让代码助手审查这段代码"）。

### 多智能体感知 CLI 参数

支持 `--agent-id` 的 CLI 子命令（默认 `default`）：`skills config/list`、`cron *`、`chats *`、`channels *`（子命令级）、`daemon status`（`daemon logs` 不支持）。
全局操作（不支持 `--agent-id`）：`qwenpaw init`、`providers`、`models`、`env`。

## spawn_subagent 子任务（当前工作区内，2.0 能力）

除跨工作区的 `chat_with_agent` 外，还可在当前项目内派生**临时子任务**（同一智能体、独立会话、完成后丢弃、不可恢复）。

| 模式 | 工作区 | 上下文 | 适用 |
|------|--------|--------|------|
| `chat_with_agent` | 目标智能体自己的工作区 | 无（纯文本） | 调用专家智能体（代码审查、文档润色等） |
| `spawn_subagent(fork=False)` | 与父任务同一项目 | 无（空白会话） | 自包含的子任务："列出 src/core 下所有 API 端点" |
| `spawn_subagent(fork=True)` | 视环境（下表） | 继承父会话全部历史 | 基于刚讨论的内容做事、可能改文件："根据我们的讨论为 parser 写单测" |

`fork=True` 行为：

| 环境 | 行为 |
|------|------|
| Coding Mode 开启 + 项目是 git 仓库 | 在 `<project_dir>/.qwenpaw/worktrees/` 建 **git worktree**，子任务在隔离 worktree 中工作 |
| Coding Mode 关闭 + 工作区是 git 仓库 | 在 `<workspace_dir>/.qwenpaw/worktrees/` 建 git worktree |
| 无 git 仓库 | **原地 fork**：继承会话上下文，与父任务同目录，无文件隔离 |

用法示例：

```python
# 前台（等待结果）
spawn_subagent(task="分析 src/core 的性能瓶颈并汇报")

# 后台（立即返回，稍后轮询）
spawn_subagent(task="扫描整个代码库的安全漏洞", background=True)
# → [TASK_ID: task-cd34]，用 check_agent_task(task_id="task-cd34") 轮询

# fork=True（git 仓库中产生隔离 worktree）
spawn_subagent(task="根据我们的讨论为 parser 写单测", fork=True)
# 有文件改动 → 保留 worktree，返回 [FORK_BRANCH: fork/xxxx]，人工 review 后合并
# 无文件改动 → worktree 自动清理
# 后台模式不自动清理 → 手动 git worktree remove .qwenpaw/worktrees/<id>
```

> `.gitignore` 忽略的文件（如 `.env`）不会进入 worktree。在项目根目录创建 `.worktreeinclude` 列出需自动拷贝的文件（每行一个路径）。

## REST API（2.0）

Base URL：`http://<host>:<port>/api` — host/port 以 `config.json` 中 `last_api` 字段（最近一次启动的地址）或 `qwenpaw daemon status` 输出为准，**不要硬编码端口**。

### 智能体管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/agents` | GET | 列出所有智能体 |
| `/api/agents` | POST | 创建智能体 |
| `/api/agents/{agent_id}` | GET | 获取智能体信息 |
| `/api/agents/{agent_id}` | PUT | 更新智能体（name/description 等） |
| `/api/agents/{agent_id}` | DELETE | 删除智能体（default 不可删） |
| `/api/agents/{agent_id}/active` | POST | 激活该智能体 |

### 智能体级 API（`X-Agent-Id` 头）

`/api/chats/*`（会话）、`/api/cron/*`（定时任务，如 `/cron/jobs`）、`/api/config/*`（渠道/心跳）、`/api/skills/*`（技能）、`/api/tools/*`（工具）、`/api/mcp/*`（MCP）、`/api/workspace*`（工作区文件，含 `/workspace/checkpoints`、`/workspace/git`）

> 注意：`/api/cron`、`/api/config` 等是前缀路由，请求需带子路径（裸前缀返回 404 属正常）。

```bash
# 获取指定智能体的会话列表
curl -H "X-Agent-Id: <agent_id>" http://<host>:<port>/api/chats

# 调用智能体 API（SSE 流式）
curl -N -X POST http://<host>:<port>/api/console/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "你好"}'
```

## 配置结构（2.0）

```
$QWENPAW_WORKING_DIR/            # 默认 ~/.qwenpaw
├── config.json                   # 全局配置（last_api、agents.active_agent、agents.profiles、browser）
└── workspaces/
    ├── default/                  # 默认智能体工作区
    │   ├── agent.json            # 智能体配置（channels/mcp/tools/security/running/heartbeat…）
    │   ├── AGENTS.md / SOUL.md   # persona 文件（手写）
    │   ├── PROFILE.md            # 系统自动生成（勿手写）
    │   ├── chats.json / jobs.json / token_usage.json   # 系统维护
    │   ├── skills/ + skill.json  # 工作区技能与启用状态
    │   └── skill_pool 之外另有 MEMORY.md、memory/ 等
    └── {agent_id}/…
$QWENPAW_SECRET_DIR/              # 默认 ~/.qwenpaw.secret（providers.json、envs.json，勿提交）
```

要点：

- 配置分两层：全局 `config.json`（provider、环境变量、智能体列表）+ 每智能体 `agent.json`
- **`agent.json` 优先级高于全局 `config.json`**；多智能体模式下所有个性化配置都放各智能体的 `agent.json`
- 修改 `agent.json`/`config.json` 后**约 2 秒自动热加载，无需重启**；保存时可能遇到 409 冲突（基于旧快照的写入被拒）→ 重新读取文件再改
- LLM 并发/限流不再是环境变量，改为 `agent.json` 的 `running` 配置：`llm_max_concurrent`（默认 10，全局共享）、`llm_max_qpm`（默认 600）、`llm_retry_enabled` 等

## 协作模式

### 1. 链式协作

```
A → B → C → 结果
```

### 2. 并行协作

```
     → A →
用户 → B → 汇总
     → C →
```

### 3. 层级协作

```
        协调者
       /  |  \
      A   B   C
```

### 4. 迭代协作

```
用户 → A → B → 审核 → (不通过) → A → ...
                          ↓ (通过)
                        结果
```

启用 `multi_agent_collaboration` 后，以上编排由智能体在对话中自动完成：用户显式指定（"让 writer 润色一下"）或智能体自主决策（判断需要某专长时主动发起）。

## 智能体角色模板

- 通用角色模板库（8 种：项目经理、数据分析师、代码审查员、用户研究员、技术架构师、测试工程师、文档工程师、DevOps 工程师）见 `TEMPLATES.md`
- 预设团队（content / dev / research）见 `multi_agent_setup.py`
- 创建时只需为智能体准备 `AGENTS.md`（职责/流程/输出格式）与 `SOUL.md`（行为原则），`PROFILE.md` 由系统生成

## 最佳实践

1. **合理规划数量**：3-5 个智能体，按职能/平台划分；空闲智能体不产生 LLM 费用
2. **写清 description**：协作时智能体靠 Name + Description + 自动生成的 PROFILE.md 选择协作对象
3. **命名清晰**：`code-reviewer` ✅ / `test1` ❌
4. **定期备份**：`cp -r ~/.qwenpaw/workspaces/<id> ~/backups/<id>-$(date +%Y%m%d)`
5. **勿删 default 智能体**（系统兜底）；删除智能体后工作区目录会保留，彻底清理需手动删除 `~/.qwenpaw/workspaces/{agent_id}`
6. **性能考量**：多智能体协作涉及多次 LLM 调用，耗时和费用高于单智能体；耗时任务用 `--background`

## 边界条件与错误处理

| 情况 | 处理 |
|------|------|
| 环境是 1.0（`copaw` CLI / `~/.copaw`） | 停止流程，引导备份并升级 CoPaw 2.0（见 Step 0） |
| CLI 未安装 / 服务未启动 | 引导 `qwenpaw init` / `qwenpaw app` |
| 智能体 ID 已存在 | 换 ID 或征询用户是否覆盖；API/Console 会返回冲突并给出建议的新名 |
| 保存配置返回 409 | 重新读取最新文件后再修改（系统拒绝基于旧快照的写入） |
| 新智能体未加载 | 先 `qwenpaw daemon reload-config` 重读配置；仍无效则按 `qwenpaw daemon restart` 打印的指引重启进程（该命令只打印指引），再重查 `qwenpaw agents list` |
| 后台任务 `failed` | 用 `--task-id` 查状态详情，结合 `qwenpaw daemon logs` 定位（可调 `QWENPAW_LOG_LEVEL=debug`） |
| 协作无响应 | 核对：双方是否都启用 `multi_agent_collaboration`、description 是否具体、`X-Agent-Id`/`--agent-id` 是否拼写正确 |
| `spawn_subagent(fork=True)` 无 git 仓库 | 属正常降级（原地 fork，无文件隔离），向用户说明 |

## 检查点（必须获得用户确认）

1. **批量创建智能体前**：展示团队规划表（ID/名称/description）
2. **删除或禁用智能体前**：明确告知影响（会话历史保留、default 不可删）
3. **直接改写 `config.json` / `agent.json` 前**：展示将写入的内容，确认后再写
4. **后台长任务派发前**：确认任务描述与目标智能体

## 安全注意事项

1. **权限隔离**：不同智能体独立渠道/技能/工具配置（`agent.json` 各自设置）
2. **数据边界**：智能体仅访问自己的工作区；跨工作区访问走协作协议
3. **密钥管理**：API key 存于 `$QWENPAW_SECRET_DIR`（默认 `~/.qwenpaw.secret`），勿提交到代码库
4. **资源限制**：通过 `agent.json → running` 的 `llm_max_concurrent` / `llm_max_qpm` 控制调用量

## FAQ

- **必须建多个智能体吗？** 不一定。单一职能用 default 即可；需要职能/平台隔离、或多平台并行时才建多个。
- **切换智能体会丢对话吗？** 不会。每个智能体的会话历史独立保存。
- **多智能体增加成本吗？** 空闲智能体不调用 LLM，不产生费用；协作时因多次调用会高于单智能体。
- **可以同时用多个智能体吗？** 可以。不同智能体绑定不同渠道（如钉钉 + Discord）时并行响应。
- **如何调试？** `qwenpaw daemon status --agent-id <id>` / `qwenpaw daemon logs`（logs 不支持 `--agent-id`），必要时 `QWENPAW_LOG_LEVEL=debug`。

## 文件索引

| 文件 | 用途 |
|------|------|
| `QUICKSTART.md` | 5 分钟搭建指南（含完整命令） |
| `TEMPLATES.md` | 8 种通用角色模板 + 场景化团队组合 |
| `multi_agent_setup.py` | 批量创建团队/智能体的自动化脚本（2.0 兼容） |
| `skill.json` | 技能启用状态与元数据 |

---

**版本：** 2.1.1（对齐 CoPaw 2.0 生态，QwenPaw 2.1.0 实测校准）
**兼容 CoPaw：** 2.0（`qwenpaw` CLI）；1.0 用户请先升级
**最后更新：** 2026-09-03
**参考文档：** [Multi-Agent](https://qwenpaw.agentscope.io/docs/multi-agent) · [Config](https://qwenpaw.agentscope.io/docs/config) · [Skills](https://qwenpaw.agentscope.io/docs/skills)