"""
AI 内容提炼服务模块
使用 CLIProxyAPI (gemini-3-pro-high) 将学生自然语言输入转换为结构化简历数据
"""
from __future__ import annotations

import json
import logging
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

# API 配置
API_BASE_URL = "http://127.0.0.1:8317/v1"
DEFAULT_MODEL = "gemini-3-pro-preview"


@dataclass
class AIConfig:
    """AI 服务配置"""
    api_key: str
    model: str = DEFAULT_MODEL
    base_url: str = API_BASE_URL
    temperature: float = 0.7
    max_tokens: int = 4000


def get_ai_config() -> AIConfig:
    """从环境变量或 Streamlit secrets 获取 AI 配置"""
    try:
        import streamlit as st
        api_key = st.secrets.get("CLIPROXY_API_KEY", os.getenv("CLIPROXY_API_KEY", ""))
        model = st.secrets.get("AI_MODEL", os.getenv("AI_MODEL", DEFAULT_MODEL))
        base_url = st.secrets.get("AI_BASE_URL", os.getenv("AI_BASE_URL", API_BASE_URL))
    except Exception:
        api_key = os.getenv("CLIPROXY_API_KEY", "")
        model = os.getenv("AI_MODEL", DEFAULT_MODEL)
        base_url = os.getenv("AI_BASE_URL", API_BASE_URL)

    return AIConfig(api_key=api_key, model=model, base_url=base_url)


# 简历提取的系统提示词
RESUME_EXTRACTION_PROMPT = """你是一个专业的简历内容提炼助手。学生会用自然语言描述他们的经历、技能和作品。

你的任务是将这些描述转换为结构化的 JSON 格式简历数据。

## 输出格式要求

必须输出以下 JSON 结构（只输出 JSON，不要其他内容）：

```json
{
    "profile": {
        "name": "姓名",
        "title": "求职意向（如：新闻记者 | 内容运营）",
        "phone": "手机号",
        "email": "邮箱",
        "wechat": "微信号",
        "location": "期望工作地点",
        "portfolio_url": "作品集链接（可选）",
        "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=默认"
    },
    "education": [
        {
            "school": "学校名称",
            "degree": "专业名称",
            "time": "2021.09 - 2025.06",
            "details": ["GPA/排名", "主修课程", "获奖情况"]
        }
    ],
    "experience": [
        {
            "company": "公司/组织名称",
            "role": "职位",
            "time": "起止时间",
            "details": ["用 STAR 法则描述的成果1", "成果2", "成果3"]
        }
    ],
    "portfolio": [
        {
            "title": "作品名称",
            "role": "你的角色",
            "link": "作品链接",
            "desc": "简短描述成果和亮点"
        }
    ],
    "skills": {
        "professional": ["专业技能1", "专业技能2"],
        "software": ["软件工具1", "软件工具2"],
        "languages": ["英语 CET-6", "粤语"]
    },
    "awards": ["获奖1", "获奖2"]
}
```

## 提炼原则

1. **量化成果**：尽量将模糊描述转换为具体数字（阅读量、增长率等）
2. **STAR 法则**：描述经历时使用 Situation-Task-Action-Result 结构
3. **关键词优化**：提取行业关键词（如 Python、数据分析、视频剪辑等）
4. **补全信息**：如果某些字段缺失，用合理的占位符标注"待补充"
5. **专业润色**：将口语化表达转换为专业简历语言

现在请处理以下学生输入：
"""


def extract_resume_from_text(
    user_input: str,
    major: str = "journalism",
    config: Optional[AIConfig] = None
) -> Dict[str, Any]:
    """
    使用 AI 从学生自然语言输入中提取结构化简历数据

    Args:
        user_input: 学生的自然语言描述
        major: 专业类型，用于调整提取策略
        config: AI 配置，默认从环境变量获取

    Returns:
        结构化的简历 JSON 数据
    """
    if config is None:
        config = get_ai_config()

    if not config.api_key:
        logger.warning("No API key configured, returning template")
        return _get_template_resume(major)

    # 构建请求
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json"
    }

    # 根据专业调整提示词
    major_hint = _get_major_hint(major)
    full_prompt = RESUME_EXTRACTION_PROMPT + f"\n\n**专业方向**: {major_hint}\n\n**学生输入**:\n{user_input}"

    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": "你是一个专业的简历内容提炼助手。只输出 JSON，不要其他内容。"},
            {"role": "user", "content": full_prompt}
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens
    }

    try:
        response = requests.post(
            f"{config.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # 提取 JSON
        resume_data = _parse_json_from_response(content)
        return resume_data

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise AIServiceError(f"AI 服务请求失败: {str(e)}")
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse AI response: {e}")
        raise AIServiceError(f"AI 响应解析失败: {str(e)}")


def _parse_json_from_response(content: str) -> Dict[str, Any]:
    """从 AI 响应中提取 JSON"""
    # 尝试直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 尝试提取 ```json ... ``` 代码块
    import re
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试找到 { ... } 结构
    brace_match = re.search(r'\{[\s\S]*\}', content)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise AIServiceError("无法从 AI 响应中提取有效的 JSON 数据")


def _get_major_hint(major: str) -> str:
    """获取专业提示"""
    hints = {
        "journalism": "新闻学 - 关注采访、写作、调查报道能力",
        "advertising": "广告学 - 关注创意策划、品牌营销、文案能力",
        "new_media": "网络与新媒体 - 关注新媒体运营、数据分析、技术能力",
        "broadcasting": "广播电视学 - 关注视频制作、导演、摄影能力"
    }
    return hints.get(major, "新闻传播学")


def _get_template_resume(major: str) -> Dict[str, Any]:
    """获取模板简历（无 API 时的降级方案）"""
    return {
        "profile": {
            "name": "待填写",
            "title": "新闻传播专业学生",
            "phone": "待填写",
            "email": "待填写",
            "wechat": "待填写",
            "location": "待填写",
            "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=default"
        },
        "education": [{
            "school": "待填写",
            "degree": "待填写",
            "time": "待填写",
            "details": ["待填写"]
        }],
        "experience": [],
        "portfolio": [],
        "skills": {
            "professional": [],
            "software": [],
            "languages": []
        },
        "awards": []
    }


def optimize_resume_section(
    section_name: str,
    section_data: Any,
    user_feedback: str,
    config: Optional[AIConfig] = None
) -> Any:
    """
    优化简历的特定部分

    Args:
        section_name: 部分名称（experience, portfolio 等）
        section_data: 当前数据
        user_feedback: 用户的优化要求
        config: AI 配置

    Returns:
        优化后的数据
    """
    if config is None:
        config = get_ai_config()

    if not config.api_key:
        return section_data

    prompt = f"""请优化以下简历的 "{section_name}" 部分。

当前内容:
{json.dumps(section_data, ensure_ascii=False, indent=2)}

用户要求:
{user_feedback}

请输出优化后的 JSON 数据（只输出 JSON，保持相同结构）："""

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": config.model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 2000
    }

    try:
        response = requests.post(
            f"{config.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return _parse_json_from_response(content)

    except Exception as e:
        logger.error(f"Section optimization failed: {e}")
        return section_data


class AIServiceError(Exception):
    """AI 服务异常"""
    pass
