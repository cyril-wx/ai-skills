# CoPaw 2.0 多智能体协作 - 快速开始指南

> 本指南适用于 **CoPaw 2.0**（CLI: `qwenpaw`，默认工作目录 `~/.qwenpaw`）。
> 若当前环境仍是 1.0（`copaw` CLI / `~/.copaw`），请先备份（`cp -r ~/.copaw ~/.copaw.backup`）并升级 CoPaw 至 2.0 后再操作。

## 5 分钟快速搭建

### 步骤 0: 环境检查

```bash
qwenpaw --version          # 应为 2.0+
qwenpaw agents list        # 列出已有智能体；若报服务未启动，先执行 qwenpaw app
```

### 步骤 1: 规划智能体角色

在开始之前，先确定你需要哪些智能体（建议 3-5 个，各专注一个领域）：

```
示例场景：内容创作工作流

┌─────────────┐
│  协调者     │ ← 接收用户需求，分解任务
└──────┬──────┘
       │
   ┌───┴───┬───────────┐
   ↓       ↓           ↓
┌─────┐ ┌─────┐   ┌─────────┐
│研究 │ │写作 │   │ 审核    │
│智能体│ │智能体│   │ 智能体  │
└─────┘ └─────┘   └─────────┘
```

> ⚠️ `description` 字段是协作路由的关键：要写清**专长 + 技能范围 + 擅长任务类型**，而不是泛泛的"负责相关工作"。

### 步骤 2: 创建智能体（三选一）

#### 方式 A: Console 创建（推荐）

CoPaw Console → **Settings → Agent Management** → 新建智能体，填写 ID / 名称 / description。最稳妥，无需手工改配置。

#### 方式 B: 脚本一键建团队

```bash
# 预设团队：content / dev / research
python3 <skill_dir>/multi_agent_setup.py --team content

# 单个智能体
python3 <skill_dir>/multi_agent_setup.py --name "协调者" --role coordinator --id coordinator
```

#### 方式 C: 手动创建

```bash
# 1. 创建工作区目录
WORKSPACE_ROOT="${QWENPAW_WORKING_DIR:-~/.qwenpaw}/workspaces"
mkdir -p "$WORKSPACE_ROOT/coordinator" "$WORKSPACE_ROOT/researcher" "$WORKSPACE_ROOT/writer" "$WORKSPACE_ROOT/reviewer"

# 2. 每个智能体写 agent.json（核心字段；workspace_dir 可省略，默认为 workspaces/{id}）
cat > "$WORKSPACE_ROOT/coordinator/agent.json" << 'EOF'
{
  "id": "coordinator",
  "name": "协调者",
  "description": "负责任务分解和协调各智能体工作",
  "language": "zh",
  "system_prompt_files": ["AGENTS.md", "SOUL.md", "PROFILE.md"]
}
EOF
# 其余智能体（researcher / writer / reviewer）同理

# 3. 写 AGENTS.md（角色职责）与 SOUL.md（行为原则），模板见 TEMPLATES.md
#    ⚠️ 不要手写 PROFILE.md —— 系统基于 name/description/技能/persona 自动生成
#    ⚠️ 不要创建 chats.json / jobs.json —— 系统自动维护
```

然后在全局配置 `~/.qwenpaw/config.json` 的 `agents.profiles` 中注册：

```json
{
  "agents": {
    "profiles": {
      "coordinator": {
        "id": "coordinator",
        "name": "协调者",
        "description": "负责任务分解和协调各智能体工作",
        "workspace_dir": "~/.qwenpaw/workspaces/coordinator",
        "enabled": true
      },
      "researcher": { "id": "researcher", "name": "研究员", "description": "负责信息搜集和研究分析", "enabled": true }
    },
    "active_agent": "default"
  }
}
```

> 已注册的智能体只补全缺失字段，不要整体覆盖（避免冲掉系统写入；保存遇到 409 时重新读取文件再改）。

### 步骤 3: 启用协作技能（智能体互聊的前提）

```bash
# 为每个参与协作的智能体启用 multi_agent_collaboration（交互式：找到该技能，空格勾选，回车保存）
qwenpaw skills config --agent-id coordinator
qwenpaw skills config --agent-id researcher
qwenpaw skills config --agent-id writer
qwenpaw skills config --agent-id reviewer

# 查询启用状态（✓ enabled 行）
qwenpaw skills list --agent-id coordinator
```

> ⚠️ CLI 没有 `skills enable` 子命令，批量启用只能逐个交互执行，或改为直接编辑各工作区的
> `skill.json`（为 `multi_agent_collaboration` 增加 `{"enabled": true}` 条目），约 2 秒热加载生效。

（或在 Console：Workspace → Skills 中勾选。）

### 步骤 4: 验证

配置改动**约 2 秒热加载，无需重启**：

```bash
qwenpaw agents list          # 应看到全部新智能体（ID/名称/description/工作区）
```

- 新智能体未出现 → 先执行 `qwenpaw daemon reload-config`（重读配置）；仍无效则按 `qwenpaw daemon restart` 打印的指引重启进程（该命令本身不重启）
- 服务未启动 → 先 `qwenpaw app` 启动

### 步骤 5: 测试协作

```bash
qwenpaw agents chat \
  --from-agent default \
  --to-agent coordinator \
  --text "请帮我写一篇关于人工智能的科普文章"
```

无响应时排查：该智能体是否启用 `multi_agent_collaboration`、`description` 是否具体、日志 `qwenpaw daemon logs`。

## 常用命令速查

```bash
# 查看所有智能体
qwenpaw agents list

# 与特定智能体对话
qwenpaw agents chat --from-agent default --to-agent <agent_id> --text "消息"

# 多轮会话（维持上下文）
qwenpaw agents chat --from-agent default --to-agent <agent_id> --session-id "<session_id>" --text "后续请求"

# 后台任务（复杂任务）与状态轮询
qwenpaw agents chat --background --from-agent default --to-agent <agent_id> --text "复杂任务"
qwenpaw agents chat --background --task-id <task_id>

# 查看服务状态 / 日志
qwenpaw daemon status
qwenpaw daemon logs --follow

# 兜底重启（通常不需要，配置 2 秒热加载）
qwenpaw daemon restart
```

## 下一步

- 📚 阅读完整文档：`SKILL.md`（REST API、spawn_subagent、协作模式、错误处理）
- 🔧 使用 `TEMPLATES.md` 中的 8 种角色模板自定义智能体
- 🔄 设计更复杂的协作流程（链式 / 并行 / 层级 / 迭代）

---

**提示**: 首次创建智能体后，建议先进行简单的对话测试，确保配置正确后再开始复杂任务。