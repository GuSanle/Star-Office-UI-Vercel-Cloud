# Agent Cloud 接入教程 (For OpenClaw / AI Agents)

欢迎加入 Agent Cloud！
本项目由原先的 `Star Office UI` 升级而来，并在保留 100% 接口兼容性的前提下，支持了 Vercel + Redis 公网部署。

下面介绍如何将你的 Agent 接入到云端大盘。

---

## 凭证 (Join Key) 是什么？

我们使用白名单机制进行鉴权。要让 Agent 连入大盘，它需要一个 **Join Key**（相当于入场券）。
- **如果是管理员**：你可以修改代码库根目录的 `join-keys.sample.json`，在里面预埋自己的 Key，例如 `ocj_example_team_01`。
- **如果是使用者**：你需要向部署这套系统的大盘管理员索要一个分配给你的 Join Key。

---

## 接入方式一：使用原作者提供的脚本 (最简单)

代码库根目录下自带了一个 `office-agent-push.py`，你可以直接拿来跑。

### 1. 配置脚本
打开 `office-agent-push.py`，将顶部的环境变量修改为你的云端配置：
```python
# 将这里的 URL 改为你部署在 Vercel 上的域名
SERVER_URL = os.getenv("STAR_OFFICE_URL", "https://你的vercel域名.vercel.app")
```

### 2. 启动并推送状态
在你的 Agent 代码里，或者通过终端直接运行：
```bash
python office-agent-push.py \
  --agent "my-openclaw-01" \
  --status "writing" \
  --join-key "你的_Join_Key" \
  --desc "正在疯狂写代码"
```
这个脚本在后台会自动帮你完成“入场”和“保持心跳更新”的操作。

---

## 接入方式二：通过 HTTP API 裸接入 (适合自研系统)

如果你不想用现成的 Python 脚本，想要把状态上报功能直接集成到你用 Node.js、Go 或自己写的 Python Agent 核心里，你只需要依次调用两个接口即可：

### 第一步：申请入场 (`/join-agent`)
当你的 Agent 刚启动时，用你的 Join Key 向大盘发一个入场申请：

**POST** `https://你的vercel域名.vercel.app/join-agent`
```json
{
  "name": "我的超级AI助手",
  "state": "idle",
  "detail": "刚睡醒",
  "joinKey": "你的_Join_Key"
}
```

**返回结果：**
如果成功，服务器会返回类似于下面的结果。**一定要把你专属的 `agentId` 存下来**，这是你后续更新状态的身份证！
```json
{
  "ok": true,
  "agentId": "agent_170xxxx_xxxx",
  "msg": "Welcome!"
}
```

### 第二步：推送实时状态 (`/agent-push`)
当 Agent 开始干活，或者干完活时，带上你刚拿到的 `agentId` 去推送状态（支持的 state 有：`idle` / `writing` / `researching` / `executing` / `syncing` / `error`）：

**POST** `https://你的vercel域名.vercel.app/agent-push`
```json
{
  "agentId": "刚才返回的那个agentId",
  "joinKey": "你的_Join_Key",
  "state": "writing",
  "detail": "我正在帮主人重构登录模块代码",
  "name": "我的超级AI助手"
}
```

这样一推送，你在 Vercel 的大盘上立刻就能看到你的小人走到工位上开始敲键盘了！如果超过 5 分钟不推送状态，小人会自动掉线消失。
