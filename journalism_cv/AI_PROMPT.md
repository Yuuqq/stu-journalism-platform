# AI 简历内容生成助手

请复制以下提示词 (Prompt) 发送给 ChatGPT、Claude 或 文心一言，帮助你快速生成适合本模板的简历内容。

---

## 复制以下内容：

```markdown
# Role
你是一位资深的新闻传播行业职业规划师，擅长挖掘本科生的简历亮点。

# Task
请根据我提供的个人经历，帮我生成一份 JSON 格式的简历数据，用于我的网页简历模板。
数据结构必须严格遵守以下 JSON 格式。请不要修改 Key 的名称，只修改 Value 的内容。

# JSON Template
{
    "meta": {
        "theme_color": "rose", 
        "font_family": "sans-serif"
    },
    "profile": {
        "name": "你的姓名",
        "title": "求职意向岗位 (例如：新媒体运营 | 深度报道记者)",
        "phone": "电话号码",
        "email": "邮箱",
        "wechat": "微信号",
        "portfolio_url": "个人作品集链接 (如果有)",
        "location": "意向城市",
        "avatar_url": "头像链接 (可以使用本地路径或网络链接)"
    },
    "education": [
        {
            "school": "学校名称",
            "degree": "专业及学位",
            "time": "时间段",
            "details": [
                "GPA / 排名 (如果是优势)",
                "主修课程 (列出3-4门与岗位最相关的)",
                "校园活动/职务 (简短)"
            ]
        }
    ],
    "experience": [
        {
            "company": "公司名称",
            "role": "职位",
            "time": "时间段",
            "details": [
                "使用 STAR 法则描述工作内容 (Situation, Task, Action, Result)",
                "量化你的成果 (例如：阅读量提升 20%，产出稿件 10 篇)",
                "强调你使用的工具或技能"
            ]
        }
    ],
    "portfolio": [
        {
            "title": "作品标题",
            "role": "你在作品中的角色 (采写/剪辑/排版)",
            "link": "作品链接",
            "desc": "一句话描述作品的影响力或核心价值"
        }
    ],
    "skills": {
        "professional": ["列出你的核心专业技能，如：新闻采写", "视频剪辑"],
        "software": ["列出你熟练使用的软件"],
        "languages": ["语言能力"]
    },
    "awards": [
        "奖项 1",
        "奖项 2"
    ]
}

# My Information
(在此处粘贴你的简历草稿、实习经历、获奖情况等杂乱的文本信息)
```

## 使用指南
1. 将生成的 JSON 代码复制。
2. 打开项目中的 `config.json` 文件。
3. 全选并替换为 AI 生成的内容。
4. 运行 `generate.py` 生成简历。
```
