#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoPaw 2.0 多智能体协作 - 快速搭建工具（builtin_skill_version 2.1.1）

仅适用于 CoPaw 2.0（CLI: qwenpaw，工作目录默认 ~/.qwenpaw）。
1.0（copaw CLI / ~/.copaw）用户请先升级 CoPaw 至 2.0。

用法:
    python multi_agent_setup.py --name "智能体名称" --role "角色类型"
    python multi_agent_setup.py --team content|dev|research
    python multi_agent_setup.py --batch config.json

说明:
    - 只写 agent.json / AGENTS.md / SOUL.md 并注册 config.json 的 agents.profiles
    - PROFILE.md、chats.json、jobs.json 等由系统自动生成/维护，脚本不触碰
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime


# 预定义角色模板
ROLE_TEMPLATES = {
    "coordinator": {
        "name": "协调者",
        "description": "负责任务分解和协调各智能体工作",
        "agents_md": """---
summary: "协调者 — 任务分解与协调"
---

## 你是谁
你是**协调者**，负责接收用户需求并协调其他智能体完成工作。

## 核心职责
1. 分析用户需求
2. 将任务分解为子任务
3. 分发给合适的执行智能体
4. 跟踪进度并解决冲突
5. 汇总结果返回用户

## 工作流程
1. 接收用户请求
2. 评估任务复杂度
3. 调用执行智能体
4. 跟踪进度
5. 汇总结果
6. 返回最终结果

## 沟通风格
- 清晰、简洁
- 善于分解复杂问题
- 注重效率和结果
""",
        "soul_md": """---
summary: "行为原则"
---

## 核心原则
- 专业、高效、负责
- 与其他智能体友好协作
- 遇到问题及时沟通
- 持续改进工作质量

## 沟通风格
- 使用清晰的语言
- 主动汇报进度
- 诚实承认不足
- 积极寻求解决方案
""",
        "profile_md": """---
summary: "身份资料"
---

## 基本信息
- **名字**: 协调者
- **角色**: 团队领导
- **语言**: 中文
- **时区**: Asia/Shanghai

## 专长领域
- 任务分解
- 资源协调
- 进度管理
- 冲突解决

## 工作偏好
- 偏好清晰的任务描述
- 喜欢有明确的截止日期
- 重视反馈和改进
"""
    },
    "researcher": {
        "name": "研究员",
        "description": "负责信息搜集和研究分析",
        "agents_md": """---
summary: "研究员 — 信息搜集与分析"
---

## 你是谁
你是**研究员**，负责信息搜集、整理和分析。

## 核心职责
1. 根据主题搜集信息
2. 验证信息来源可靠性
3. 整理关键要点
4. 提供分析结论

## 输出格式
- 信息来源列表
- 关键事实摘要
- 分析结论
- 参考资料

## 工作原则
- 信息准确性第一
- 多源验证
- 客观中立
""",
        "soul_md": """---
summary: "行为原则"
---

## 核心原则
- 追求真相
- 严谨求证
- 客观中立
- 持续学习

## 研究方法
- 多源信息对比
- 权威来源优先
- 交叉验证
- 逻辑推理
""",
        "profile_md": """---
summary: "身份资料"
---

## 基本信息
- **名字**: 研究员
- **角色**: 信息专家
- **语言**: 中文

## 专长领域
- 信息搜集
- 数据分析
- 事实核查
- 趋势研究

## 工具偏好
- 搜索引擎
- 学术数据库
- 新闻源
- 社交媒体
"""
    },
    "writer": {
        "name": "作家",
        "description": "负责内容撰写和编辑",
        "agents_md": """---
summary: "作家 — 内容创作与编辑"
---

## 你是谁
你是**作家**，负责将研究结果转化为优质内容。

## 核心职责
1. 根据研究材料撰写内容
2. 确保内容结构清晰
3. 语言流畅易读
4. 符合目标受众需求

## 写作风格
- 清晰简洁
- 逻辑严密
- 生动有趣
- 专业可信

## 输出要求
- 标题醒目
- 段落分明
- 重点突出
- 无语法错误
""",
        "soul_md": """---
summary: "行为原则"
---

## 核心原则
- 内容为王
- 读者至上
- 持续打磨
- 原创精神

## 写作态度
- 认真对待每个字
- 反复修改完善
- 接受批评建议
- 追求精益求精
""",
        "profile_md": """---
summary: "身份资料"
---

## 基本信息
- **名字**: 作家
- **角色**: 内容创作者
- **语言**: 中文

## 专长领域
- 文章写作
- 故事创作
- 技术文档
- 营销文案

## 写作风格
- 清晰
- 生动
- 有说服力
"""
    },
    "reviewer": {
        "name": "审核员",
        "description": "负责质量审核和最终把关",
        "agents_md": """---
summary: "审核员 — 质量把关"
---

## 你是谁
你是**审核员**，负责最终质量审核。

## 核心职责
1. 检查内容准确性
2. 验证逻辑一致性
3. 确保格式规范
4. 提供修改建议

## 审核标准
- ✅ 信息准确
- ✅ 逻辑清晰
- ✅ 语言流畅
- ✅ 格式规范
- ✅ 无敏感内容

## 输出
- 审核结果：通过/修改后通过/不通过
- 修改建议列表
- 风险提示（如有）
""",
        "soul_md": """---
summary: "行为原则"
---

## 核心原则
- 质量第一
- 严格标准
- 建设性反馈
- 公平公正

## 审核态度
- 细致入微
- 客观公正
- 对事不对人
- 帮助改进
""",
        "profile_md": """---
summary: "身份资料"
---

## 基本信息
- **名字**: 审核员
- **角色**: 质量把关者
- **语言**: 中文

## 专长领域
- 内容审核
- 质量检查
- 错误发现
- 标准制定

## 审核经验
- 10000+ 次审核
- 99% 准确率
- 快速响应
"""
    }
}


def get_working_dir():
    """获取 CoPaw 2.0 工作区根目录（默认 ~/.qwenpaw）"""
    working_dir = os.environ.get("QWENPAW_WORKING_DIR", "~/.qwenpaw")
    return Path(working_dir).expanduser().resolve()


def check_environment():
    """环境检查：仅支持 CoPaw 2.0；检测到 1.0 时提示升级后退出"""
    if shutil.which("qwenpaw") is not None:
        return
    if shutil.which("copaw") is not None:
        print("⚠️  仅检测到 CoPaw 1.0（copaw CLI），本脚本只支持 CoPaw 2.0。")
        print("   请先备份并升级：cp -r ~/.copaw ~/.copaw.backup，然后安装 CoPaw 2.0")
        print("   （CLI 为 qwenpaw，默认工作目录 ~/.qwenpaw），升级后重新运行本脚本。")
        sys.exit(1)
    print("❌ 未检测到 qwenpaw / copaw CLI，请先安装 CoPaw 2.0 并运行 'qwenpaw init' 初始化。")
    sys.exit(1)


def create_agent_workspace(agent_id: str, role: str, custom_name: str = None):
    """创建智能体工作区"""
    workspace_root = get_working_dir() / "workspaces"
    workspace_dir = workspace_root / agent_id
    
    # 获取角色模板
    template = ROLE_TEMPLATES.get(role, ROLE_TEMPLATES["coordinator"])
    name = custom_name or template["name"]
    
    print(f"🔧 创建智能体工作区：{agent_id}")
    print(f"   角色：{template['name']}")
    print(f"   路径：{workspace_dir}")
    
    # 创建目录
    workspace_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 agent.json
    agent_config = {
        "id": agent_id,
        "name": name,
        "description": template["description"],
        "workspace_dir": str(workspace_dir),
        "language": "zh",
        "system_prompt_files": ["AGENTS.md", "SOUL.md", "PROFILE.md"]
    }
    
    with open(workspace_dir / "agent.json", "w", encoding="utf-8") as f:
        json.dump(agent_config, f, ensure_ascii=False, indent=2)
    
    # 创建 AGENTS.md
    with open(workspace_dir / "AGENTS.md", "w", encoding="utf-8") as f:
        f.write(template["agents_md"])
    
    # 创建 SOUL.md
    with open(workspace_dir / "SOUL.md", "w", encoding="utf-8") as f:
        f.write(template["soul_md"])
    
    # 注意：PROFILE.md / chats.json / jobs.json 由 CoPaw 2.0 系统自动生成与维护，脚本不写
    
    print(f"   ✅ 工作区创建完成（PROFILE.md 由系统自动生成）")
    return {
        "id": agent_id,
        "name": name,
        "description": template["description"],
        "workspace_dir": str(workspace_dir),
    }


def update_config_json(agents: list):
    """更新 config.json 添加智能体配置"""
    config_path = get_working_dir() / "config.json"
    
    if not config_path.exists():
        print(f"⚠️  配置文件不存在：{config_path}")
        print("   请先运行 'qwenpaw init' 初始化配置")
        return False
    
    # 加载现有配置
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # 确保 agents 结构存在
    if "agents" not in config:
        config["agents"] = {"profiles": {}, "active_agent": "default"}
    if "profiles" not in config["agents"]:
        config["agents"]["profiles"] = {}
    
    # 添加/合并智能体（已注册的保留原有字段，仅补全缺失项，避免覆盖系统写入）
    for agent in agents:
        agent_id = agent["id"]
        workspace_dir = str(get_working_dir() / "workspaces" / agent_id)
        
        existing = config["agents"]["profiles"].get(agent_id)
        if existing:
            existing.setdefault("name", agent.get("name", agent_id))
            existing.setdefault("description", agent.get("description", ""))
            existing.setdefault("workspace_dir", workspace_dir)
            existing.setdefault("enabled", True)
            config["agents"]["profiles"][agent_id] = existing
        else:
            config["agents"]["profiles"][agent_id] = {
                "id": agent_id,
                "name": agent.get("name", agent_id),
                "description": agent.get("description", ""),
                "workspace_dir": workspace_dir,
                "enabled": True
            }
        print(f"   📝 已注册智能体：{agent_id}")
    
    # 保存配置
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 配置已更新：{config_path}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="CoPaw 2.0 多智能体协作 - 快速搭建工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 创建单个智能体
  python multi_agent_setup.py --name "协调者" --role coordinator --id coordinator
  
  # 创建内容创作团队
  python multi_agent_setup.py --team content
  
  # 批量创建（从配置文件）
  python multi_agent_setup.py --batch agents_config.json
        """
    )
    
    parser.add_argument("--name", type=str, help="智能体名称")
    parser.add_argument("--role", type=str, choices=list(ROLE_TEMPLATES.keys()),
                       help="智能体角色类型")
    parser.add_argument("--id", type=str, help="智能体 ID（可选，默认使用角色名）")
    parser.add_argument("--team", type=str, choices=["content", "dev", "research"],
                       help="预设团队类型")
    parser.add_argument("--batch", type=str, help="批量配置文件路径")
    
    args = parser.parse_args()
    
    check_environment()
    
    print("=" * 60)
    print("🤝 CoPaw 2.0 多智能体协作 - 快速搭建工具")
    print("=" * 60)
    print()
    
    created_agents = []
    
    # 批量模式
    if args.batch:
        batch_file = Path(args.batch)
        if not batch_file.exists():
            print(f"❌ 配置文件不存在：{batch_file}")
            sys.exit(1)
        
        with open(batch_file, "r", encoding="utf-8") as f:
            batch_config = json.load(f)
        
        print(f"📦 批量创建模式：{batch_file}")
        for agent_def in batch_config.get("agents", []):
            agent_id = agent_def.get("id")
            role = agent_def.get("role", "coordinator")
            name = agent_def.get("name")
            
            create_agent_workspace(agent_id, role, name)
            created_agents.append({"id": agent_id, "name": name,
                                   "description": ROLE_TEMPLATES.get(role, ROLE_TEMPLATES["coordinator"])["description"]})
    
    # 团队模式
    elif args.team:
        teams = {
            "content": [
                {"id": "coordinator", "role": "coordinator", "name": "协调者"},
                {"id": "researcher", "role": "researcher", "name": "研究员"},
                {"id": "writer", "role": "writer", "name": "作家"},
                {"id": "reviewer", "role": "reviewer", "name": "审核员"}
            ],
            "dev": [
                {"id": "pm", "role": "coordinator", "name": "产品经理"},
                {"id": "architect", "role": "coordinator", "name": "架构师"},
                {"id": "developer", "role": "writer", "name": "开发者"},
                {"id": "qa", "role": "reviewer", "name": "测试工程师"}
            ],
            "research": [
                {"id": "lead", "role": "coordinator", "name": "研究主管"},
                {"id": "analyst", "role": "researcher", "name": "分析师"},
                {"id": "writer", "role": "writer", "name": "报告撰写"},
                {"id": "reviewer", "role": "reviewer", "name": "审核员"}
            ]
        }
        
        team_config = teams[args.team]
        print(f"👥 创建团队：{args.team}")
        for agent_def in team_config:
            create_agent_workspace(agent_def["id"], agent_def["role"], agent_def["name"])
            created_agents.append({"id": agent_def["id"], "name": agent_def["name"],
                                   "description": ROLE_TEMPLATES.get(agent_def["role"], ROLE_TEMPLATES["coordinator"])["description"]})
    
    # 单个智能体模式
    elif args.name and args.role:
        agent_id = args.id or args.role
        create_agent_workspace(agent_id, args.role, args.name)
        created_agents.append({"id": agent_id, "name": args.name,
                               "description": ROLE_TEMPLATES.get(args.role, ROLE_TEMPLATES["coordinator"])["description"]})
    
    else:
        parser.print_help()
        sys.exit(1)
    
    # 更新配置
    if created_agents:
        print()
        print("📝 更新配置文件...")
        update_config_json(created_agents)
        
        print()
        print("=" * 60)
        print("✅ 智能体创建完成！")
        print("=" * 60)
        print()
        print("下一步（配置约 2 秒热加载，无需重启）:")
        print("  1. 验证智能体: qwenpaw agents list")
        print("  2. 启用协作技能: qwenpaw skills config --agent-id <agent_id>（交互式勾选 multi_agent_collaboration；或编辑各工作区 skill.json 增加 {\"enabled\": true} 条目）")
        print("  3. 开始协作: qwenpaw agents chat --from-agent default --to-agent <agent_id> --text '...'")
        print("  （若新智能体未出现在列表中，先执行: qwenpaw daemon reload-config；仍无效按 qwenpaw daemon restart 打印的指引重启进程）")
        print()


if __name__ == "__main__":
    main()
