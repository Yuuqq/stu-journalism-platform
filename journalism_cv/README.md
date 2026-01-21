# 新闻传播专业 AI 简历模板 (Journalism CV Template)

这是一个专为新闻传播学本科生设计的毕业季简历模板，注重展示**作品集 (Portfolio)**、**专业技能**和**实习经历**。

项目包含一个 Python 生成器，可将配置数据转换为精美的 HTML 简历（可直接打印为 PDF）。

## ✨ 特性

*   **作品集优先**：专门的板块展示你的报道、视频或设计作品。
*   **配置分离**：所有内容都在 `config.json` 中修改，无需触碰代码。
*   **AI 辅助**：提供 `AI_PROMPT.md`，复制提示词给 ChatGPT/Claude，自动帮你润色并生成 JSON 数据。
*   **专业排版**：基于 Tailwind CSS 的 A4 纸张布局，简洁、现代、重点突出。

## 📁 目录结构

*   `config.json`: 简历的内容数据（在这里修改你的信息）。
*   `template.html`: 简历的排版模板（如果你懂 HTML 可以修改样式）。
*   `generate.py`: 生成脚本。
*   `AI_PROMPT.md`: 这是一个 Prompt，教你如何用 AI 帮你写简历。

## 🚀 快速开始

### 1. 准备环境
你需要安装 Python。如果没有安装，请先下载安装。
然后安装模板引擎库：
```bash
pip install jinja2
```

### 2. 生成简历
直接运行脚本：
```bash
python generate.py
```
成功后，会生成一个 `my_cv.html` 文件。

### 3. 预览与导出
1. 双击打开 `my_cv.html`（推荐使用 Chrome 或 Edge 浏览器）。
2. 按 `Ctrl + P` (打印)。
3. **关键设置**：
    *   目标打印机选择：**另存为 PDF**。
    *   纸张尺寸：**A4**。
    *   边距：**无** (或 "最小值")。
    *   选项：**勾选 "背景图形" (Background graphics)** <--- 非常重要！
4. 保存即可。

## 📝 如何修改内容

**方法 A：手动修改**
用记事本或代码编辑器打开 `config.json`，按照里面的格式修改为你自己的信息。

**方法 B：AI 自动生成 (推荐)**
1. 打开 `AI_PROMPT.md`。
2. 复制里面的 Prompt。
3. 发送给 ChatGPT/Claude，并附上你的原始经历。
4. 将 AI 返回的 JSON 代码覆盖到 `config.json` 中。

## 🎨 修改配色
在 `config.json` 的 `meta` 字段中，虽然预留了 `theme_color`，但目前的 CSS 模板使用的是 Tailwind 的 `rose` 色系。
如果你想修改颜色，可以在 `template.html` 中搜索 `rose` 并替换为 `blue`, `indigo`, `teal` 等 Tailwind 颜色名称。
