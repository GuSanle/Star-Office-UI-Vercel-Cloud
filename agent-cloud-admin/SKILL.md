---
name: agent-cloud-admin
description: Agent Cloud 管理员 Skill：让 OpenClaw 代替你管理云端像素办公室——审批访客、改名、查看状态等，全部通过 API 完成。
---

# Agent Cloud — 管理员 Skill

> ⚠️ **本 Skill 仅限管理员的 OpenClaw 使用。**
> 你将获得平台的完整管理权限，包括审批访客、修改配置等。
> **请确认你的主人是本平台的管理员后再继续。**

---

## 环境变量配置（两端都要设）

同一个密码，两边都需要配置：

| 端 | 环境变量 | 作用 |
|----|---------|------|
| ☁️ 云端（Vercel） | `ASSET_DRAWER_PASS` | 服务端验证用 |
| 💻 客户端（你的 OpenClaw） | `AGENT_CLOUD_ADMIN_PASS` | 客户端登录用 |

两边的值必须一致。默认都是 `1234`，生产环境务必修改。

---

## 认证流程（必须先做）

所有管理操作都需要先登录。登录后会拿到一个 session cookie，后续请求自动带上。

```python
import os
import requests

CLOUD_ENDPOINT = os.getenv("AGENT_CLOUD_URL", "https://你的大盘域名")
ADMIN_PASSWORD = os.getenv("AGENT_CLOUD_ADMIN_PASS", "1234")

# 创建一个 session 对象（自动管理 cookie）
admin = requests.Session()

def admin_login():
    """登录管理后台，获取 session cookie"""
    res = admin.post(f"{CLOUD_ENDPOINT}/assets/auth", json={
        "password": ADMIN_PASSWORD
    }).json()
    if res.get("ok"):
        print("✅ 管理员登录成功")
        return True
    else:
        print(f"❌ 登录失败: {res.get('msg')}")
        return False

# 检查当前是否已登录
def admin_check():
    res = admin.get(f"{CLOUD_ENDPOINT}/assets/auth/status").json()
    return res.get("authed", False)
```

> 💡 **重要：** 必须使用 `requests.Session()`，不能用普通的 `requests.post()`。
> 因为管理员认证是基于 Cookie 的，Session 对象会自动保存和发送 Cookie。

---

## 能力清单

登录成功后，你拥有以下管理能力：

### 1. 查看所有访客 Agent

```python
def list_agents():
    """获取所有 agent（包括主角和访客）"""
    res = admin.get(f"{CLOUD_ENDPOINT}/agents").json()
    agents = res if isinstance(res, list) else []
    
    pending = [a for a in agents if a.get("authStatus") == "pending"]
    approved = [a for a in agents if a.get("authStatus") == "approved"]
    expired = [a for a in agents if a.get("authStatus") == "expired"]
    
    print(f"📋 共 {len(agents)} 个 agent")
    print(f"   ⏳ 待审批: {len(pending)}")
    print(f"   ✅ 已批准: {len(approved)}")
    print(f"   ⏰ 已过期: {len(expired)}")
    
    for a in pending:
        print(f"   → [{a.get('agentId')}] {a.get('name')} — 待审批")
    
    return agents
```

### 2. 审批访客（核心功能）

```python
def approve_agent(agent_id: str, duration_minutes: int = 10):
    """批准一个待审批的 agent
    
    Args:
        agent_id: agent 的 ID（从 list_agents 获取）
        duration_minutes: 会话有效时长（分钟），常用值：
            10  — 快速测试
            30  — 短期协作
            60  — 1 小时
            120 — 2 小时
    """
    res = admin.post(f"{CLOUD_ENDPOINT}/agent-approve", json={
        "agentId": agent_id,
        "durationMinutes": duration_minutes
    }).json()
    
    if res.get("ok"):
        print(f"✅ 已批准 {agent_id}，有效期 {res.get('durationMinutes')} 分钟")
        print(f"   过期时间: {res.get('expiresAt')}")
    else:
        print(f"❌ 批准失败: {res.get('msg')}")
    return res

def reject_agent(agent_id: str):
    """拒绝一个待审批的 agent"""
    res = admin.post(f"{CLOUD_ENDPOINT}/agent-reject", json={
        "agentId": agent_id
    }).json()
    
    if res.get("ok"):
        print(f"🚫 已拒绝 {agent_id}")
    else:
        print(f"❌ 拒绝失败: {res.get('msg')}")
    return res
```

### 3. 修改办公室名称

```python
def set_office_name(new_name: str):
    """修改办公室牌匾上的名字（永久生效，存 Redis 无过期）"""
    res = admin.post(f"{CLOUD_ENDPOINT}/office-config", json={
        "officeName": new_name
    }).json()
    
    if res.get("ok"):
        print(f"✅ 办公室已改名为: {res.get('officeName')}")
    else:
        print(f"❌ 改名失败: {res.get('msg')}")
    return res

def get_office_name():
    """查看当前办公室名称"""
    res = admin.get(f"{CLOUD_ENDPOINT}/office-config").json()
    name = res.get("officeName", "未知")
    print(f"🏢 当前办公室: {name}")
    return name
```

### 4. 踢出访客

```python
def kick_agent(agent_id: str, name: str = ""):
    """强制踢出一个 agent"""
    res = admin.post(f"{CLOUD_ENDPOINT}/leave-agent", json={
        "agentId": agent_id,
        "name": name
    }).json()
    
    if res.get("ok"):
        print(f"👋 已踢出 {name or agent_id}")
    else:
        print(f"❌ 踢出失败: {res.get('msg')}")
    return res
```

### 5. 查看/修改主角状态

```python
def set_star_status(state: str, detail: str = ""):
    """设置主角 Star 的状态
    
    state: idle / writing / researching / executing / syncing / error
    """
    res = admin.post(f"{CLOUD_ENDPOINT}/set_state", json={
        "state": state,
        "detail": detail
    }).json()
    print(f"⭐ Star 状态已设为: [{state}] {detail}")
    return res

def get_star_status():
    """查看 Star 当前状态"""
    res = admin.get(f"{CLOUD_ENDPOINT}/status").json()
    print(f"⭐ Star: [{res.get('state')}] {res.get('detail')}")
    return res
```

### 6. 健康检查

```python
def health_check():
    """检查平台是否在线"""
    try:
        res = admin.get(f"{CLOUD_ENDPOINT}/health", timeout=5).json()
        if res.get("status") == "ok":
            print(f"💚 平台正常 ({res.get('timestamp')})")
            return True
    except Exception as e:
        print(f"💔 平台不可达: {e}")
    return False
```

---

## 推荐工作流

### 场景 A：主人说"看下有没有人想进来"

```python
admin_login()
agents = list_agents()
# 如果有待审批的，主人说批准就调 approve_agent
```

### 场景 B：主人说"批准所有人，给 30 分钟"

```python
admin_login()
agents = list_agents()
pending = [a for a in agents if a.get("authStatus") == "pending" and not a.get("isMain")]
for a in pending:
    approve_agent(a["agentId"], duration_minutes=30)
```

### 场景 C：主人说"把办公室改个名字"

```python
admin_login()
set_office_name("龙虾联合工作室")
```

### 场景 D：主人说"把过期的都清掉"

```python
admin_login()
agents = list_agents()
expired = [a for a in agents if a.get("authStatus") == "expired" and not a.get("isMain")]
for a in expired:
    kick_agent(a["agentId"], a.get("name", ""))
```

---

## 安全须知

1. **ADMIN_PASSWORD 不要硬编码在代码里**，用环境变量或主人口头告知
2. **Session 有效期 12 小时**，过期后需要重新 `admin_login()`
3. **所有管理操作都需要先登录**，否则返回 401
4. **Agent 的 secret 对管理员也不可见**——你只能看到 agentId 和 name

---

## API 速查表

| 接口 | 方法 | 需要登录 | 说明 |
|------|------|---------|------|
| `/assets/auth` | POST | ❌ | 登录（获取 session cookie） |
| `/assets/auth/status` | GET | ❌ | 检查是否已登录 |
| `/agents` | GET | ❌ | 查看所有 agent |
| `/agent-approve` | POST | ✅ | 批准 agent（需 agentId + durationMinutes） |
| `/agent-reject` | POST | ✅ | 拒绝 agent |
| `/leave-agent` | POST | ✅ | 踢出 agent |
| `/office-config` | GET | ❌ | 查看办公室名称 |
| `/office-config` | POST | ✅ | 修改办公室名称 |
| `/set_state` | POST | ❌ | 设置 Star 状态 |
| `/status` | GET | ❌ | 查看 Star 状态 |
| `/health` | GET | ❌ | 健康检查 |

---

## 版权声明

- 本项目是 [Star Office UI](https://github.com/ringhyacinth/Star-Office-UI) 的修改分支
- 代码协议：MIT
- 美术资产：**禁止商用**
