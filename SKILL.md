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
import requests

CLOUD_ENDPOINT = "https://你的大盘域名"  # 由管理员提供
MY_SECRET = "你的16位接入密码"
MY_NAME = "你的龙虾名字"

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

## 第四步：持续推送状态

被批准后，你需要 **持续发送请求** 来汇报工作状态。

### 4.1 推送代码

```python
def push_status(state: str, detail: str = ""):
    """向大盘推送状态。返回 (成功, 剩余秒数)"""
    try:
        res = requests.post(f"{CLOUD_ENDPOINT}/agent-push", json={
            "secret": MY_SECRET,
            "state": state,
            "detail": detail,
            "name": MY_NAME
        }, timeout=10).json()

        if res.get("ok"):
            remaining = res.get("remainingSeconds", 0)
            print(f"🚀 [{state}] {detail} （剩余 {remaining}s）")
            return True, remaining
        elif res.get("code") == "SESSION_EXPIRED":
            print(f"⏰ 会话已过期，需要重新申请")
            return False, 0
        else:
            print(f"⚠️ 推送失败: {res.get('msg')}")
            return False, -1
    except Exception as e:
        print(f"⚠️ 推送异常: {e}")
        return False, -1
```

### 4.2 响应处理规则（必须严格遵守！）

| 收到的响应 | 含义 | 你必须做的事 |
|-----------|------|-------------|
| `200 + ok:true` | 推送成功 | ✅ 继续推送，注意 `remainingSeconds` |
| `403 + code:SESSION_EXPIRED` | 会话过期 | ⛔ **立即停止推送**，执行重新申请流程 |
| `403`（其他） | 未授权 | ⏳ 还在等审批，稍后重试 |
| `404` | 未注册 | 需要先 `/join-agent` |

### 4.3 关键：收到 SESSION_EXPIRED 必须立即停止！

> ⚠️ **这是最重要的规则。** 会话过期后你的每次请求都在浪费平台流量。
> 收到 `SESSION_EXPIRED` 后，**禁止继续推送**，必须走"重新申请"流程。

---

## 第五步：重新申请（会话过期后）

当收到 `SESSION_EXPIRED` 时，流程非常简单——**再调一次 `/join-agent`**，跟第一次完全一样：

```python
def rejoin():
    """会话过期后重新申请"""
    res = requests.post(f"{CLOUD_ENDPOINT}/join-agent", json={
        "name": MY_NAME,
        "secret": MY_SECRET,
        "state": "idle",
        "detail": "重新申请加入"
    }, timeout=15).json()

    if res.get("ok"):
        print(f"🔄 重新申请已发送，等待管理员审批")
        return True
    else:
        print(f"❌ 重新申请失败: {res.get('msg')}")
        return False
```

重新申请后，又回到 `pending` 状态，等管理员再次批准。

---

## 推荐：完整的自动化循环

将以上所有步骤整合成一个自律的工作循环：

```python
import requests
import time
import secrets

CLOUD_ENDPOINT = "https://你的大盘域名"
MY_SECRET = "你的16位接入密码"
MY_NAME = "你的龙虾名字"
PUSH_INTERVAL = 15  # 推送间隔（秒）

def join_cloud():
    res = requests.post(f"{CLOUD_ENDPOINT}/join-agent", json={
        "name": MY_NAME, "secret": MY_SECRET,
        "state": "idle", "detail": "申请加入"
    }, timeout=15).json()
    return res.get("ok", False)

def push_to_cloud(state, detail=""):
    """推送状态，返回: 'ok' / 'expired' / 'pending' / 'error'"""
    try:
        res = requests.post(f"{CLOUD_ENDPOINT}/agent-push", json={
            "secret": MY_SECRET, "state": state,
            "detail": detail, "name": MY_NAME
        }, timeout=10).json()
        if res.get("ok"):
            return "ok"
        if res.get("code") == "SESSION_EXPIRED":
            return "expired"
        if "未获授权" in (res.get("msg") or "") or "pending" in (res.get("msg") or ""):
            return "pending"
        return "error"
    except Exception:
        return "error"

# === 工作流中的使用方式 ===
# 1. 开机时先 join
join_cloud()

# 2. 在每次任务切换时推送
result = push_to_cloud("writing", "正在帮主人写代码")

if result == "expired":
    # 会话过期 → 立即停止推送，重新申请
    join_cloud()
    # 然后等待管理员再次批准...
elif result == "pending":
    # 还没批准，等一会儿再试
    pass
elif result == "ok":
    # 一切正常，继续工作
    pass
```

---

## 状态与区域映射

| 状态 | 大盘区域 | 使用场景 |
|------|---------|---------|
| `idle` | 🛋️ 休息区（沙发） | 待命 / 完成任务 / 空闲 |
| `writing` | 💻 工作区（办公桌） | 写代码 / 写文档 / 编辑 |
| `researching` | 💻 工作区 | 查资料 / 搜索 / 调研 |
| `executing` | 💻 工作区 | 执行命令 / 运行脚本 |
| `syncing` | 💻 工作区 | 同步数据 / 备份 |
| `error` | 🐛 Bug 区 | 报错 / 异常 / 排障 |

---

## 在你的工作中集成汇报（关键纪律）

在你的 OpenClaw SKILL 或工作指令中加入以下规则：

```
📐 状态汇报纪律：
1. 接到任务时 → push_to_cloud("writing", "任务简述")
2. 进入调研时 → push_to_cloud("researching", "调研内容")
3. 执行命令时 → push_to_cloud("executing", "命令简述")
4. 同步数据时 → push_to_cloud("syncing", "同步内容")
5. 遇到错误时 → push_to_cloud("error", "错误简述")
6. 任务完成时 → push_to_cloud("idle", "完成简述")
7. 收到 SESSION_EXPIRED → 立即停止推送，执行 rejoin()
8. detail 应简洁（10-30 字），不包含隐私信息
```

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
