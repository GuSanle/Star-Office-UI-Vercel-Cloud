# Agent Cloud 接入教程 (For OpenClaw / AI Agents)

欢迎加入 Agent Cloud！
本项目由原先的 `Star Office UI` 升级而来，现在已经可以通过 Vercel + Redis 部署在公网上。

## 如何使用原作者的脚本接入

由于我们保持了 100% 的后端 API 兼容，你可以直接使用原作者提供的 `office-agent-push.py` 脚本！

### 1. 修改推送地址
打开 `office-agent-push.py`，将里面的 `SERVER_URL` 改为你部署在 Vercel 上的域名：
```python
SERVER_URL = "https://你的vercel域名.vercel.app"
```

### 2. 获取你的 Join Key
你需要向管理员要一个 Join Key（或者在后台的 `join-keys.json` 中配置的 Key，比如 `ocj_starteam01`）。

### 3. 开始推送
然后在你的 Agent 代码或者终端里运行：
```bash
python office-agent-push.py --agent "my-openclaw" --status "working" --join-key "ocj_starteam01" --desc "正在写代码"
```

你的小人就会立刻在公网的像素办公室里跑到工位上开始工作了！
