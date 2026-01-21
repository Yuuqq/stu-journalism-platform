"""
学生成长数字孪生页面
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.config import get_config
from core.data_manager import get_data_manager


def render_digital_twin():
    """渲染数字孪生页面"""
    st.header("📊 学生成长数字孪生 (Digital Twin)")

    config = get_config()
    data_mgr = get_data_manager()

    # 检查能力矩阵是否加载
    if not config.competency_matrix:
        st.error("找不到能力矩阵配置文件")
        return

    # ==================== 学生选择器 ====================
    st.subheader("👤 学生档案选择")

    students = data_mgr.get_available_students()
    selected_key = st.selectbox(
        "选择要分析的学生档案",
        options=list(students.keys()),
        format_func=lambda x: students[x]
    )

    # ==================== 数据加载与分析 ====================
    history_scores = []

    if selected_key == "current":
        # 实时模式：分析当前编辑中的简历
        history_scores = _analyze_current_cv(data_mgr)
        st.info(
            "💡 **实时反馈模式**：系统正在分析您在 [智能简历工坊] 中编辑的内容。\n"
            "试着去 Tab 1 添加技能关键词（如 Python, 视频），雷达图将实时更新。"
        )
    else:
        # 历史存档模式
        history_scores = _analyze_student_history(data_mgr, selected_key)

    if not history_scores:
        st.warning("该学生尚无历史档案数据。")
        return

    # ==================== 可视化展示 ====================
    df_history = pd.DataFrame(history_scores)
    latest_scores = history_scores[-1]

    col1, col2 = st.columns([1, 1])

    with col1:
        _render_radar_chart(latest_scores, students[selected_key])

    with col2:
        _render_growth_chart(df_history)

    # ==================== AI 反馈 ====================
    _render_feedback(data_mgr, latest_scores)


def _analyze_current_cv(data_mgr) -> list:
    """分析当前编辑中的简历"""
    if 'cv_data' not in st.session_state:
        st.session_state.cv_data = data_mgr.get_default_cv_config()

    cv_data = st.session_state.cv_data
    scores = data_mgr.calculate_competency_scores(cv_data, "journalism")
    scores['Stage'] = "当前编辑版本"

    return [scores]


def _analyze_student_history(data_mgr, student_id: str) -> list:
    """分析学生历史档案"""
    history = data_mgr.load_student_history(student_id)
    scores_list = []

    for i, data in enumerate(history):
        version = data.get('_version', f'v{i+1}')
        scores = data_mgr.calculate_competency_scores(data, "journalism")
        scores['Stage'] = f"阶段 {version.upper()}"
        scores_list.append(scores)

    return scores_list


def _render_radar_chart(scores: dict, title: str):
    """渲染能力雷达图"""
    st.subheader("1. 核心胜任力雷达 (Latest)")

    categories = [k for k in scores.keys() if k != 'Stage']
    r_values = [scores[k] for k in categories]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=r_values,
        theta=categories,
        fill='toself',
        name='当前水平',
        line_color='rgb(99, 110, 250)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        showlegend=False,
        title=f"{title} - 能力维度图"
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_growth_chart(df_history: pd.DataFrame):
    """渲染成长轨迹图"""
    st.subheader("2. 成长轨迹演进 (History)")

    df_melted = df_history.melt(
        id_vars=['Stage'],
        var_name='Dimension',
        value_name='Score'
    )

    fig = px.line(
        df_melted,
        x='Stage',
        y='Score',
        color='Dimension',
        markers=True
    )

    fig.update_layout(title="跨学期能力增长曲线")
    st.plotly_chart(fig, use_container_width=True)


def _render_feedback(data_mgr, scores: dict):
    """渲染 AI 反馈"""
    st.subheader("3. AI 辅助评价 (System Feedback)")

    feedback = data_mgr.get_competency_feedback(scores)

    st.success(f"✅ **能力亮点**：{feedback['highlight']}")
    st.info(f"💡 **提升建议**：{feedback['suggestion']}")
