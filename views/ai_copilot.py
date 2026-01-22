"""
AI 教学助教页面

提供基于 RAG 的智能问答功能。
"""
from __future__ import annotations

import streamlit as st

from core.rag_engine import get_rag_engine, RAGEngine


@st.cache_resource(show_spinner="正在加载知识库...")
def _get_cached_rag_engine() -> RAGEngine:
    """获取缓存的 RAG 引擎实例

    使用 Streamlit 的 cache_resource 装饰器确保
    RAG 引擎只初始化一次，避免重复加载语料库。
    """
    return get_rag_engine()


def render_ai_copilot():
    """渲染 AI 教学助教页面"""
    st.header("🤖 AI 教学助教 (Teaching Copilot)")
    st.caption("内置《新闻学概论》、《传播学教程》及大厂 JD 知识库")

    col_chat, col_context = st.columns([2, 1])

    # ==================== 右栏: 学习资源 ====================
    with col_context:
        _render_learning_resources()

    # ==================== 左栏: 聊天界面 ====================
    with col_chat:
        _render_chat_interface()


def _render_learning_resources():
    """渲染学习资源推荐"""
    st.subheader("📚 推荐学习资源")

    st.markdown("""
    根据你的简历短板，为你推荐：

    **📖 阅读**
    - 《精确新闻报道》 (Philip Meyer) - *针对数据分析能力*
    - 普利策奖非虚构写作特稿选 - *针对叙事能力*

    **▶️ 课程**
    - [Coursera] Python for Data Science
    - [Bilibili] 财新视频部：如何做短视频叙事
    """)

    st.info(
        "💡 **提问提示**：\n"
        "- '如何用 STAR 法则优化我的实习经历？'\n"
        "- '什么是倒金字塔结构？'\n"
        "- '做数据新闻需要学什么？'"
    )

    # 显示 RAG 引擎状态
    _render_rag_status()


def _render_rag_status():
    """渲染 RAG 引擎状态"""
    with st.expander("🔧 知识库状态"):
        try:
            engine = _get_cached_rag_engine()
            stats = engine.get_stats()

            if stats['indexed']:
                st.success(f"✅ 已索引 {stats['total_chunks']} 个文本块")
                st.write(f"来源文件: {stats['total_files']} 个")
                for f in stats['files']:
                    st.caption(f"  - {f}")
            else:
                st.warning("⚠️ 知识库尚未索引")
        except Exception as e:
            st.error(f"引擎状态获取失败: {e}")


def _render_chat_interface():
    """渲染聊天界面"""
    # 初始化聊天历史
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": "你好！我是你的 AI 教学助手。关于新闻采写、简历优化或课程知识点，随时问我。"
            }
        ]

    # 显示历史消息
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 输入框
    if prompt := st.chat_input("向 AI 助教提问..."):
        _handle_user_input(prompt)


def _handle_user_input(prompt: str):
    """处理用户输入"""
    # 添加用户消息
    st.session_state.chat_history.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # 生成 AI 回复
    with st.chat_message("assistant"):
        with st.spinner("正在检索课程资料..."):
            response_text = _query_knowledge_base(prompt)
        st.markdown(response_text)

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response_text
    })


def _query_knowledge_base(query: str) -> str:
    """查询知识库

    Args:
        query: 用户查询

    Returns:
        AI 生成的回复
    """
    try:
        engine = _get_cached_rag_engine()
        return engine.generate_response(query)
    except Exception as e:
        return f"⚠️ RAG 引擎运行出错: {str(e)}"
