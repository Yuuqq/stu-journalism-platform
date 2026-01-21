# 部署指南：汕大新闻学院简历生成器

本项目已配置为 **Streamlit Web 应用**，您可以选择以下两种方式供学生使用。

## 方案一：部署到 Streamlit Cloud (免费、最推荐)

这是最简单、最稳定的方式。学生不需要安装任何东西，只需访问一个网址。

### 步骤：
1.  **上传代码到 GitHub**：
    *   将整个 `CV` 文件夹上传到您的 GitHub 仓库（确保包含 `app.py`, `requirements.txt` 和 `journalism_cv/` 文件夹）。
2.  **注册 Streamlit Cloud**：
    *   访问 [share.streamlit.io](https://share.streamlit.io/)。
    *   使用 GitHub 账号登录。
3.  **创建应用**：
    *   点击 "New app"。
    *   选择刚才的 GitHub 仓库。
    *   **Main file path** 填写：`app.py`。
    *   点击 "Deploy"。
4.  **分发链接**：
    *   部署成功后，您会获得一个 `https://your-app.streamlit.app` 的链接。
    *   直接把这个链接发给学生即可。

---

## 方案二：本地运行 (适合机房或个人电脑)

如果您希望在实验室电脑上运行，或者学生想在自己电脑上离线使用。

### 步骤：
1.  安装 Python。
2.  打开终端，安装依赖：
    ```bash
    pip install streamlit jinja2
    ```
3.  运行应用：
    ```bash
    streamlit run app.py
    ```
4.  浏览器会自动打开 `http://localhost:8501`，即可使用。

---

## 💡 学生使用流程

1.  **选择专业**：在左侧侧边栏选择 "广告学"、"新闻学" 等，系统会自动切换到对应的 **配色** 和 **排版布局**。
2.  **加载数据**：点击 "加载专业示例数据"，选择一个模板（如 "陈创意"），点击覆盖。
3.  **编辑内容**：在中间的文本框中，直接修改 JSON 内容（改名字、改经历）。
4.  **下载简历**：点击右侧的 **"📥 下载 HTML 简历"** 按钮。
5.  **导出 PDF**：打开下载的 HTML 文件，按 `Ctrl + P`，选择 "另存为 PDF"（记得勾选 "背景图形"）。
