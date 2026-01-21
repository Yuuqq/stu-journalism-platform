# 汕头大学新闻学院专属简历模板

本项目专为**汕头大学长江新闻与传播学院**学子定制，包含四个热门专业的简历范例。

## 🎓 包含的专业模板 (Demos)

1.  **广告学 (Advertising)**
    *   **文件**: `cv_advertising.html` / `config_advertising.json`
    *   **特点**: 强调创意策划、AE 执行、品牌公关、视觉设计能力。
    *   **色调**: Rose (玫瑰红) - 热情、活力。

2.  **网络与新媒体 (Network & New Media)**
    *   **文件**: `cv_new_media.html` / `config_new_media.json`
    *   **特点**: 强调数据分析、用户增长、内容运营、产品思维、Python/SQL 技能。
    *   **色调**: Teal (青色) - 科技、理性。

3.  **新闻学 (Journalism)**
    *   **文件**: `cv_journalism.html` / `config_journalism.json`
    *   **特点**: 强调深度报道、采访写作、新闻敏感度、摄影作品。
    *   **色调**: Indigo (靛蓝) - 专业、稳重。

4.  **广播电视学 (Broadcasting & Hosting)**
    *   **文件**: `cv_broadcasting.html` / `config_broadcasting.json`
    *   **特点**: 强调视频编导、后期剪辑 (Pr/Ae/FCP)、脚本分镜、现场调度。
    *   **色调**: Violet (紫罗兰) - 艺术、创造力。

## 🚀 如何使用

### 方法一：直接查看范例
在浏览器中直接打开对应的 `.html` 文件即可查看效果。

### 方法二：制作自己的简历 (推荐)
1.  **选择模板**: 找到与你专业最接近的 `config_xxx.json` 文件。
2.  **复制文件**: 将其复制并重命名为 `config.json` (或者直接在原文件上修改)。
3.  **修改内容**: 用记事本打开，替换里面的姓名为你自己的信息。
4.  **生成简历**: 
    在终端运行：
    ```bash
    python generate.py
    ```
    (或者指定文件生成: `python generate.py config_advertising.json my_ad_cv.html`)
5.  **导出 PDF**: 打开生成的 HTML，Ctrl+P 打印 -> 另存为 PDF (记得勾选“背景图形”)。

## 💡 给汕大学弟学妹的建议
*   **作品集 (Portfolio)** 是核心！请在 `portfolio` 字段中放入你大学四年最拿得出手的作品链接（如微信推文、B站视频、设计作品集链接）。
*   **数据化成果**: 实习经历中尽量用数据说话（如“阅读量 10w+”、“转化率提升 20%”）。
*   **技能差异化**: 
    *   广告学同学多展示 4A 实习经历和全案策划能力。
    *   网新同学多展示数据分析和工具使用能力。
    *   新闻学同学展示扎实的文字功底和重磅稿件。
    *   广电同学展示视频制作的全流程掌控力。

祝大家求职顺利！
