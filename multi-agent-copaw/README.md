# CoPaw 2.0 多智能体协作技能 (multi-agent-copaw)

🤝 **快速搭建和管理 CoPaw 2.0 多智能体协作系统**（`builtin_skill_version: 2.1`）

> 本技能仅支持 **CoPaw 2.0**（CLI: `qwenpaw`，默认工作目录 `~/.qwenpaw`）。
> 1.0（`copaw` CLI / `~/.copaw`）用户请先备份并升级 CoPaw 至 2.0。

---

## 📖 概述

本技能提供完整的工具集和模板，帮助用户快速搭建 CoPaw 2.0 多智能体协作系统。通过本技能，您可以：

- ✅ 快速创建多个具有不同角色的智能体（Console / 脚本 / 手动三种方式）
- ✅ 启用 `multi_agent_collaboration` 协作技能，打通智能体间通信
- ✅ 使用预定义的角色模板（AGENTS.md / SOUL.md；PROFILE.md 由系统自动生成）
- ✅ 通过 `chat_with_agent` 进行跨智能体协作（实时 / 多轮 / 后台任务）
- ✅ 通过 `spawn_subagent` 在当前项目内派生子任务（支持 git worktree 隔离）

---

## 🚀 快速开始

### 方式 1: 使用 Python 脚本（推荐）

```bash
# 创建内容创作团队（4 个智能体）
python3 ~/.qwenpaw/workspaces/default/skills/multi-agent-copaw/multi_agent_setup.py --team content

# 创建开发团队 / 研究团队
python3 ~/.qwenpaw/workspaces/default/skills/multi-agent-copaw/multi_agent_setup.py --team dev
python3 ~/.qwenpaw/workspaces/default/skills/multi-agent-copaw/multi_agent_setup.py --team research

# 创建单个智能体
python3 ~/.qwenpaw/workspaces/default/skills/multi-agent-copaw/multi_agent_setup.py \
  --name "我的智能体" \
  --role coordinator \
  --id my_agent
```

> 脚本运行前会检查 `qwenpaw` CLI；若仅检测到 1.0（`copaw`）会提示升级并退出。
> 非默认工作目录时设置 `QWENPAW_WORKING_DIR` 即可。

### 方式 2: Console 创建

CoPaw Console → Settings → Agent Management → 新建智能体（推荐，最稳妥）。

### 方式 3: 手动创建

参考 [`QUICKSTART.md`](./QUICKSTART.md) 详细步骤。

---

## 📁 文件结构

```
multi-agent-copaw/
├── SKILL.md              # 技能完整文档（2.0 流程、REST API、spawn_subagent、错误处理）
├── QUICKSTART.md         # 5 分钟快速开始指南
├── TEMPLATES.md          # 角色模板库
├── multi_agent_setup.py  # 自动化搭建脚本
├── skill.json            # 技能配置
└── README.md             # 本文件
```

---

## 🎭 预定义角色

| 角色 | ID | 职责 |
|------|-----|------|
| 协调者 | coordinator | 任务分解与协调 |
| 研究员 | researcher | 信息搜集与分析 |
| 作家 | writer | 内容创作与编辑 |
| 审核员 | reviewer | 质量审核与把关 |

---

## 👥 预设团队

### 内容创作团队 (content)

```
协调者 → 研究员 → 作家 → 审核员
```

适用于：文章写作、报告生成、内容创作等场景。

### 开发团队 (dev)

```
产品经理 → 架构师 → 开发者 → 测试工程师
```

适用于：软件开发、代码审查、技术文档等场景。

### 研究团队 (research)

```
研究主管 → 分析师 → 报告撰写 → 审核员
```

适用于：市场调研、数据分析、学术研究等场景。

> 建议团队规模 **3-5 个智能体**；每个智能体的 `description` 要写清专长，它是协作路由的关键。

---

## 💬 智能体通信

### CLI 方式（`chat_with_agent`）

```bash
# 智能体 A 与智能体 B 对话（新建会话，实时模式）
qwenpaw agents chat \
  --from-agent default \
  --to-agent coordinator \
  --text "请帮我写一篇关于 AI 的文章"

# 多轮会话（维持上下文）
qwenpaw agents chat \
  --from-agent default \
  --to-agent researcher \
  --session-id "<session_id>" \
  --text "请深入分析第一点的来源"

# 后台任务（复杂任务）与状态轮询
qwenpaw agents chat --background --from-agent default --to-agent writer --text "生成长报告"
qwenpaw agents chat --background --task-id <task_id>
```

### REST API 方式（2.0）

> 端口不要硬编码，以 `~/.qwenpaw/config.json` 的 `last_api` 或 `qwenpaw daemon status` 为准。
> 智能体级 API 需携带 `X-Agent-Id` 头。

```bash
# 列出所有智能体
curl http://127.0.0.1:<port>/api/agents

# 智能体对话（SSE 流式）
curl -N http://127.0.0.1:<port>/api/console/chat \
  -H "Content-Type: application/json" \
  -H "X-Agent-Id: coordinator" \
  -d '{"input": "请开始任务"}'
```

---

## 📊 协作模式

### 链式协作

```
A → B → C → 结果
```

### 并行协作

```
     → A →
用户 → B → 汇总
     → C →
```

### 层级协作

```
        协调者
       /  |  \
      A   B   C
```

### 迭代协作

```
用户 → A → B → 审核 → (不通过) → A → ...
                          ↓ (通过)
                        结果
```

---

## 🔧 常用命令

```bash
# 查看所有智能体
qwenpaw agents list

# 启用协作技能（交互式：找到 multi_agent_collaboration，空格勾选，回车保存）
qwenpaw skills config --agent-id <agent_id>

# 查询技能启用状态（✓ enabled 行）
qwenpaw skills list --agent-id <agent_id>

# 查看服务状态 / 日志
qwenpaw daemon status
qwenpaw daemon logs --follow

# 兜底重启（配置约 2 秒热加载，通常无需重启）
qwenpaw daemon restart
```

---

## 📚 文档链接

- [完整技能文档](./SKILL.md) - 2.0 工作流、REST API 参考、spawn_subagent、错误处理
- [快速开始指南](./QUICKSTART.md) - 5 分钟搭建教程
- [角色模板库](./TEMPLATES.md) - 8 种通用角色模板
- [CoPaw 官方多智能体文档](https://qwenpaw.agentscope.io/docs/multi-agent)

---

## 🛠️ 自定义角色

1. 复制 `TEMPLATES.md` 中的角色模板
2. 修改角色定义：`AGENTS.md`（职责）与 `SOUL.md`（行为原则）——**不要手写 PROFILE.md**，系统会自动生成
3. 运行搭建脚本或在 Console 创建智能体
4. 启用协作技能并测试

---

## ⚠️ 注意事项

1. **工作区隔离**: 每个智能体有独立工作区 `workspaces/{agent_id}/`（删除智能体后工作区仍保留）
2. **会话管理**: 使用 `--session-id` 续聊、`--background` + `--task-id` 追踪后台任务
3. **配置生效**: 改动约 2 秒热加载；保存遇 409 时重新读取文件再改（系统拒绝基于旧快照的写入）
4. **限流配置**: LLM 并发/限流在 `agent.json` 的 `running` 配置（`llm_max_concurrent` 默认 10、`llm_max_qpm` 默认 600），不再是环境变量
5. **勿删 default 智能体**；空闲智能体零成本
6. **安全边界**: 不同智能体使用不同的 API 密钥

---

## 📝 更新日志

### v2.1 (2026-09-03)

- ✅ 全面适配 CoPaw 2.0（`qwenpaw` CLI、`~/.qwenpaw` 目录、新 REST API `/api/agents` + `X-Agent-Id`）
- ✅ 1.0 用户引导升级（环境探测 + 备份升级提示）；不再兼容 1.0
- ✅ PROFILE.md 改为系统自动生成，脚本与指南不再手写
- ✅ 新增协作技能启用流程（`qwenpaw skills enable multi_agent_collaboration --agent-id`）
- ✅ 新增 `spawn_subagent`、后台任务（`--background`/`--task-id`）、热加载（约 2 秒）说明
- ✅ 搭建脚本 `multi_agent_setup.py` 适配 2.0（环境检查、profile 合并注册）
- ✅ 修复 README 中的错误硬编码路径（`/app/working/...` → `~/.qwenpaw/...`）

### v1.0 (2026-04-02)

- ✅ 初始版本发布（CoPaw 1.0）
- ✅ 4 种预定义角色
- ✅ 3 种预设团队
- ✅ 自动化搭建脚本
- ✅ 完整文档

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 改进本技能！

---

**兼容 CoPaw**: 2.0（`qwenpaw` CLI）；1.0 用户请先升级  
**最后更新**: 2026-09-03  
**作者**: CoPaw Community