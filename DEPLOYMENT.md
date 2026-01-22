# Streamlit Cloud 部署指南

本文档说明如何将 AI 赋能教学实验平台部署到 Streamlit Cloud。

## 前置要求

1. GitHub 账号
2. Streamlit Cloud 账号（使用 GitHub 登录）
3. CLIProxyAPI 密钥（用于 AI 功能）

## 部署步骤

### 1. 将代码推送到 GitHub

```bash
# 初始化 Git（如果尚未初始化）
git init

# 添加所有文件
git add .

# 提交
git commit -m "准备部署到 Streamlit Cloud"

# 添加远程仓库
git remote add origin https://github.com/your-username/cv-platform.git

# 推送
git push -u origin main
```

### 2. 在 Streamlit Cloud 创建应用

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 点击 "New app"
3. 选择你的 GitHub 仓库
4. 配置：
   - **Main file path**: `app.py`
   - **Python version**: 3.10 或更高

### 3. 配置 Secrets

在 Streamlit Cloud 应用设置中，添加以下 Secrets：

```toml
# CLIProxyAPI 密钥
CLIPROXY_API_KEY = "your-actual-api-key"

# AI 模型
AI_MODEL = "gemini-3-pro-high"
```

**获取 API 密钥**：
- 访问 https://help.router-for.me/cn/management/api
- 注册并获取 API 密钥

### 4. 部署

点击 "Deploy" 按钮，等待部署完成。

## 文件结构说明

```
CV/
├── app.py                    # 主入口
├── requirements.txt          # Python 依赖
├── .streamlit/
│   ├── config.toml          # Streamlit 配置
│   └── secrets.toml.example # Secrets 模板
├── core/
│   ├── config.py            # 配置管理
│   ├── data_manager.py      # 数据管理
│   ├── ai_service.py        # AI 服务
│   ├── rag_engine.py        # RAG 引擎
│   └── user_manager.py      # 用户管理
├── views/
│   ├── resume_builder.py    # 简历工坊
│   ├── digital_twin.py      # 数字孪生
│   └── ai_copilot.py        # AI 助教
├── assets/
│   ├── cv_configs/          # 简历配置
│   ├── cv_templates/        # HTML 模板
│   └── corpus/              # RAG 语料库
└── data/
    └── students/            # 学生数据
```

## 数据持久化说明

⚠️ **重要**：Streamlit Cloud 使用临时文件系统，应用重启后本地文件会丢失。

对于生产环境，建议：
1. 使用外部数据库（如 Supabase、Firebase）
2. 或使用云存储（如 Google Cloud Storage）

当前版本使用本地 JSON 文件存储，适合演示和测试。

## 常见问题

### Q: AI 功能无法使用
A: 检查 Secrets 中的 `CLIPROXY_API_KEY` 是否配置正确。

### Q: 页面加载缓慢
A: 首次加载会初始化 RAG 引擎，稍后会更快。

### Q: 如何添加管理员账号
A: 在 `data/users.json` 中手动添加用户，设置 `"role": "admin"`。

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 创建 secrets 文件
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# 编辑 secrets.toml，填入你的 API 密钥

# 运行
streamlit run app.py
```

## 技术支持

如有问题，请联系开发团队。
