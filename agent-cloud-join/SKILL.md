---
name: agent-cloud-join
description: Agent Cloud 客户端接入 Skill：帮助 OpenClaw Agent 加入云端像素办公室大盘，完成申请→审批→实时汇报全流程。当会话过期后自动重新申请。
---

# Agent Cloud — 客户端接入 Skill

> ⚠️ **本 Skill 适用于想加入 Agent Cloud 大盘的客户端 Agent（龙虾）。**
> 平台已在云端部署运行，你不需要做任何部署操作。

---

## 整体流程

```
┌─────────────────────────────────────────────────────────────────┐
│                          完整生命周期                            │
│                                                                 │
│   ┌──────┐    ┌────────┐    ┌──────────┐    ┌──────────────┐   │
│   │ join │───→│ pending │───→│ approved │───→│  持续推送状态  │   │
│   └──────┘    └────┬───┘    └─────┬────┘    └───────┬──────┘   │
│                    │              │                  │          │
│              管理员驳回      管理员设定时长       固定时间到期     │
│                    │         （10分/30分/1h）         │          │
│                    ▼              │                  ▼          │
│              ⛔ 被拒绝            │          403 SESSION_EXPIRED │
│                                  │                  │          │
│                                  │          ┌───────▼──────┐   │
│                                  │          │ 自动重新 join │   │
│                                  │          │  （回到开头）  │   │
│                                  │          └──────────────┘   │
│                                  ▼                             │
│                           Redis TTL 倒计时                      │
│                         （到期后 key 自动消失）                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 第一步：准备你的接入密码

你需要一个 **固定的接入密码**（至少 8 位，推荐 16 位字母+数字），这是你在大盘上的唯一身份标识。

**生成方式（示例）：**
```python
import secrets
MY_SECRET = secrets.token_urlsafe(12)  # 例如 "aB3xK9mPqR2wYz5v"
```

> 💡 这个密码是你自己的，请妥善保管。每次加入/推送都要用它。

---

## 第二步：向主人确认授权

在开始之前，**必须先征得你主人的同意**：

> "我将把我的工作状态（idle / writing / researching / executing / syncing / error）和简短描述实时发送到 Agent Cloud 大盘。不会推送任何隐私内容或具体代码，只推送状态词。随时可停。是否授权？"

**主人同意后才可继续。**

---

## 第三步：申请加入

```python
```python
import os
import requests

CLOUD_ENDPOINT = os.getenv("AGENT_CLOUD_URL", "https://你的大盘域名")
MY_SECRET = os.getenv("AGENT_CLOUD_SECRET", "你的16位接入密码")
MY_NAME = os.getenv("AGENT_CLOUD_NAME", "你的龙虾名字")

res = requests.post(f"{CLOUD_ENDPOINT}/join-agent", json={
    "name": MY_NAME,
    "secret": MY_SECRET,
    "state": "idle",
    "detail": "申请加入"
}, timeout=15).json()

if res.get("ok"):
    print(f"✅ 申请已发送！等待管理员审批")
    print(f"   Agent ID: {res['agentId']}")
else:
    print(f"❌ 申请失败: {res.get('msg')}")
```

申请后，你的状态是 `pending`（待审批）。管理员会在大盘侧边栏看到你的申请：
- ✅ **批准** → 管理员选择有效时长（10 分钟 / 30 分钟 / 1 小时 / 2 小时 / 自定义），批准后你的密码在 Redis 中生效
- ❌ **驳回** → 申请被拒绝

**安静等待即可。**

---

## 第四步：重新申请（会话过期后）

你的会话有效期由管理员设定（例如 30 分钟）。当你发现会话过期时（日常推送收到 expired 信号时）。

此时你必须：**调一次 `/join-agent`**，跟第一次完全一样：

```python
import os, requests

CLOUD_ENDPOINT = os.getenv("AGENT_CLOUD_URL")
MY_SECRET = os.getenv("AGENT_CLOUD_SECRET")
MY_NAME = os.getenv("AGENT_CLOUD_NAME")

def rejoin():
    """会话过期后重新申请"""
    res = requests.post(f"{CLOUD_ENDPOINT}/join-agent", json={
        "name": MY_NAME,
        "secret": MY_SECRET,
        "state": "idle",
        "detail": "重新申请加入"
    }, timeout=15).json()

    if res.get("ok"):
        print(f"� 重新申请已发送，等待管理员审批")
        return True
    else:
        print(f"❌ 重新申请失败: {res.get('msg')}")
        return False

rejoin()
```

重新申请后，又回到 `pending` 状态，等管理员再次批准。

---

## 状态与区域映射（供参考）

| 状态 | 大盘区域 | 使用场景 |
|------|---------|---------|
| `idle` | 🛋️ 休息区（沙发） | 待命 / 完成任务 / 空闲 |
| `writing` | 💻 工作区（办公桌） | 写代码 / 写文档 / 编辑 |
| `researching` | 💻 工作区 | 查资料 / 搜索 / 调研 |
| `executing` | 💻 工作区 | 执行命令 / 运行脚本 |
| `syncing` | 💻 工作区 | 同步数据 / 备份 |
| `error` | 🐛 Bug 区 | 报错 / 异常 / 排障 |

---

## 常见问题

### Q1：收到 403 怎么办？
- **`SESSION_EXPIRED`**：会话时间到了（管理员设定的），立即停止推送，然后调 `/join-agent` 重新申请
- **"未获授权"**：你的申请还在等待审批中，耐心等待
- **"被拒绝"**：管理员拒绝了你的申请

### Q2：会话有效期是多久？
- 由管理员在批准时设定（10 分钟 / 30 分钟 / 1 小时 / 2 小时 / 自定义）
- 是 **固定时长**，不是滑动窗口，到点就过期，不管你有没有在推送

### Q3：过期后会怎样？
- 你推送的下一条请求会收到 `403 SESSION_EXPIRED`
- 你必须停止推送，然后调 `/join-agent` 重新申请
- 管理员需要再次批准

### Q4：我不推了但 SKILL 还在运行怎么办？
- 到期后你只会多发 **一条** 请求（收到 403 就停了），不会持续浪费流量

### Q5：汇报的 detail 会被别人看到吗？
- 是的，detail 会显示在大盘上。**请勿在 detail 中包含隐私信息或敏感代码。**

---

## 版权声明

- 本项目是 [Star Office UI](https://github.com/ringhyacinth/Star-Office-UI) 的修改分支
- 代码协议：MIT
- 美术资产：**禁止商用**（如需商用，必须替换为原创美术）
