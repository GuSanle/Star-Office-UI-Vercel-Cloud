# Agent Cloud - Vercel 部署指南

由于我们已经对原生架构进行了 Redis 拦截（Monkey Patching），现在你可以不修改任何 API，非常轻松地将其部署到 Vercel 上。

## 前置准备

1. **注册 Vercel 账号**：前往 [vercel.com](https://vercel.com) 并使用 GitHub 账号登录。

---

## 步骤 1：在 Vercel 部署项目

你可以通过 **Vercel CLI** 部署，或者通过 **GitHub 关联** 部署。

### 通过 GitHub 自动部署 (最简单)
1. 将本地修改 Commit 并推送到你自己的 GitHub 仓库。
2. 登录 Vercel 控制台，点击 **Add New -> Project**。
3. 导入你的 GitHub 仓库。
4. 在 **Environment Variables (环境变量)** 区域，配置以下两个必须的安全变量：
   - `FLASK_SECRET_KEY` = `(随便写一段长一点的随机字符串，保证 Flask Session 安全)`
   - `ASSET_DRAWER_PASS` = `(设置一个你的后台管理抽屉密码，必须>=8位)`
5. 点击 **Deploy**。此时应用可以启动，但还缺少 Redis 持久化存储。

---

## 步骤 2：添加 Redis 数据库 (必须)

由于 Vercel 是无状态的 Serverless 环境，我们必须使用一个外部的 Redis 来存储 `state.json` 的数据。你有两种方式接入：

### 方式 A：使用 Vercel Storage KV（推荐，全自动免密配置）
1. 在你的 Vercel 项目控制台，点击顶部的 **Storage** 标签。
2. 选择 **Create Database -> KV** (底层也是 Upstash 提供的服务)。
3. 同意协议并创建。
4. 创建成功后，Vercel 会自动向你的项目环境里注入名叫 `KV_URL` 的环境变量。
5. **我们代码底层的 `redis_utils.py` 会自动识别这个变量，你不需要做任何额外配置！**

### 方式 B：手动使用独立的 Upstash 账号
如果你之前在 [upstash.com](https://upstash.com) 自己建了数据库：
1. 登录 Upstash 控制台，找到你数据库的 **REST API / Connection / Node / Python** 的 `redis://` 格式的连接串。
2. 回到 Vercel 项目的 **Settings -> Environment Variables**。
3. 新增一个环境变量 `REDIS_URL`，把刚才的连接串填进去。
4. 点击顶部的 **Deployments**，对最新的一次部署点击三个点，选择 **Redeploy** 让环境变量生效。

---

## 步骤 3：验证部署是否成功

Vercel 会为你分配一个域名（例如 `https://agent-cloud.vercel.app`）。

你可以直接打开这个域名，你应该就能看到原始熟悉的 **Star Office 像素大厅**，并且由于有了 Redis 持久化，你的数据即使 Vercel 实例冻结也不会丢失！
