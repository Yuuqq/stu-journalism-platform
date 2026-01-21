import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
from datetime import datetime, timedelta
from jinja2 import Template

# --- 配置与初始化 ---
st.set_page_config(layout="wide", page_title="汕大新闻学院数智化教学平台", page_icon="🎓")

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "你好！我是你的 AI 教学助手。关于新闻采写、简历优化或课程知识点，随时问我。"}
    ]

from rag_engine import get_rag_engine

# 模板映射
template_map = {
    "modern": "template.html",
    "classic": "template_classic.html",
    "agency": "template_agency.html",
    "visual": "template_visual.html"
}

# --- 辅助函数 ---

def load_template(layout):
    """加载 HTML 模板"""
    filename = template_map.get(layout, 'template.html')
    path = os.path.join('journalism_cv', filename)

    # 如果找不到，回退到默认
    if not os.path.exists(path):
        path = os.path.join('journalism_cv', 'template.html')
        
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def query_rag_knowledge_base(query):
    """
    调用本地 RAG 引擎进行真实检索
    """
    try:
        engine = get_rag_engine()
        return engine.generate_response(query)
    except Exception as e:
        return f"⚠️ RAG 引擎运行出错: {str(e)}"

# --- 模块一：简历生成器 (保留原有逻辑) ---
def render_resume_builder():
    st.header("📝 智能简历工坊")
    
    # 侧边栏移到这里，只针对此 Tab 生效（或保持全局）
    # 为避免冲突，这里使用两列布局而不是侧边栏
    
    col_config, col_editor, col_preview = st.columns([1, 2, 2])
    
    with col_config:
        st.subheader("🎨 风格配置")
        major_preset = st.selectbox(
            "选择专业 (自动推荐风格)",
            ["自定义", "广告学 (Agency)", "新闻学 (Classic)", "网新 (Modern)", "广播电视 (Visual)"],
            key="res_major"
        )
        
        # 预设逻辑
        defaults = {"layout": "modern", "theme": "rose", "font": "sans"}
        if major_preset == "广告学 (Agency)": defaults = {"layout": "agency", "theme": "luxury", "font": "sans"}
        elif major_preset == "新闻学 (Classic)": defaults = {"layout": "classic", "theme": "academic", "font": "serif"}
        elif major_preset == "网新 (Modern)": defaults = {"layout": "modern", "theme": "teal", "font": "sans"}
        elif major_preset == "广播电视 (Visual)": defaults = {"layout": "visual", "theme": "violet", "font": "sans"}

        layout = st.selectbox("排版布局", ["modern", "classic", "agency", "visual"], index=["modern", "classic", "agency", "visual"].index(defaults['layout']), key="res_layout")
        theme_color = st.selectbox("配色主题", ["rose", "teal", "indigo", "violet", "academic", "luxury"], index=["rose", "teal", "indigo", "violet", "academic", "luxury"].index(defaults['theme']), key="res_theme")
        font_family = st.radio("字体风格", ["sans", "serif"], index=0 if defaults['font'] == "sans" else 1, key="res_font")

        st.markdown("---")
        with st.expander("📂 加载示例数据"):
            demo_choice = st.selectbox("选择示例", ["当前数据", "广告学示例", "网新示例", "新闻学示例", "广电示例"], key="res_demo")
            if st.button("加载数据", key="res_load_btn"):
                path_map = {
                    "广告学示例": 'journalism_cv/config_advertising.json',
                    "网新示例": 'journalism_cv/config_new_media.json',
                    "新闻学示例": 'journalism_cv/config_journalism.json',
                    "广电示例": 'journalism_cv/config_broadcasting.json'
                }
                if demo_choice in path_map:
                    with open(path_map[demo_choice], 'r', encoding='utf-8') as f:
                        st.session_state.cv_data = json.load(f)
                        st.rerun()

    with col_editor:
        st.subheader("✏️ 数据编辑")
        if 'cv_data' not in st.session_state:
            with open('journalism_cv/config_advertising.json', 'r', encoding='utf-8') as f:
                st.session_state.cv_data = json.load(f)
        
        edited_data_str = st.text_area("JSON 编辑器", value=json.dumps(st.session_state.cv_data, indent=4, ensure_ascii=False), height=600, key="res_json_editor")
        
        try:
            current_data = json.loads(edited_data_str)
            # 更新 Session State
            st.session_state.cv_data = current_data
            # 注入 Meta
            current_data['meta'] = {'layout': layout, 'theme_color': theme_color, 'font_family': font_family}
        except:
            st.error("JSON 格式错误")
            current_data = st.session_state.cv_data

    with col_preview:
        st.subheader("👁️ 实时预览")
        template_content = load_template(layout)
        template = Template(template_content)
        html_output = template.render(**current_data)
        
        st.download_button("📥 下载简历 (HTML)", html_output, file_name="resume.html", mime="text/html", type="primary")
        st.components.v1.html(html_output, height=800, scrolling=True)

# --- 模块二：数字孪生 (Digital Twin) ---

def calculate_competency_scores(cv_data, matrix, major='journalism'):
    """基于关键词匹配计算各项能力分数"""
    scores = {}
    dimensions = matrix.get(major, {}).get('dimensions', {})
    baseline = matrix.get(major, {}).get('baseline_score', 60)
    
    # 提取简历中所有文本内容
    text_blob = json.dumps(cv_data, ensure_ascii=False).lower()
    
    for dim_id, dim_info in dimensions.items():
        match_count = 0
        for kw in dim_info['keywords']:
            if kw.lower() in text_blob:
                match_count += 1
        
        # 计算得分：基准分 + 关键词加分 (最高100)
        score = baseline + (match_count * 5)
        scores[dim_info['label']] = min(score, 100)
        
    return scores

def render_digital_twin():
    st.header("📊 学生成长数字孪生 (Digital Twin)")
    
    # 1. 加载配置矩阵
    try:
        with open('config/competency_matrix.json', 'r', encoding='utf-8') as f:
            matrix = json.load(f)
    except:
        st.error("找不到能力矩阵配置文件")
        return

    # 2. 学生选择器
    st.subheader("👤 学生档案选择")
    student_names = {
        "current": "📝 当前编辑中 (实时分析 Tab 1 数据)", 
        "zhang": "Zhang X霸 (模拟-学霸型)", 
        "li": "Li 导演 (模拟-特长型)", 
        "wang": "Wang 逆袭 (模拟-进步型)"
    }
    selected_key = st.selectbox("选择要分析的学生档案", options=list(student_names.keys()), format_func=lambda x: student_names[x])

    # 3. 加载数据
    history_scores = []
    
    if selected_key == "current":
        # 实时模式：读取 Session State
        if 'cv_data' not in st.session_state:
            # 防御性加载：如果用户直接刷新页面进入 Tab 2，加载默认值
            with open('journalism_cv/config_advertising.json', 'r', encoding='utf-8') as f:
                st.session_state.cv_data = json.load(f)

        data = st.session_state.cv_data
        scores = calculate_competency_scores(data, matrix, 'journalism')
        scores['Stage'] = "当前编辑版本"
        history_scores.append(scores)

        st.info("💡 **实时反馈模式**：系统正在分析您在 [智能简历工坊] 中编辑的内容。试着去 Tab 1 添加技能关键词（如 Python, 视频），雷达图将实时更新。")

    else:
        # 历史存档模式：读取 data/students/*.json
        stages = ["v1", "v2", "v3"]
        for stage in stages:
            file_path = f"data/students/config_{selected_key}_{stage}.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    latest_data = data 
                    scores = calculate_competency_scores(data, matrix, 'journalism')
                    scores['Stage'] = f"阶段 {stage.upper()}"
                    history_scores.append(scores)

    if not history_scores:
        st.warning("该学生尚无历史档案数据。")
        return

    df_history = pd.DataFrame(history_scores)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. 核心胜任力雷达 (Latest)")
        # 仅展示最新阶段的雷达图
        latest_scores = history_scores[-1]
        categories = [k for k in latest_scores.keys() if k != 'Stage']
        r_values = [latest_scores[k] for k in categories]
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=r_values,
            theta=categories,
            fill='toself',
            name='当前水平'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            title=f"{student_names[selected_key]} - 能力维度图"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        st.subheader("2. 成长轨迹演进 (History)")
        # 转换数据格式以适应折线图
        df_melted = df_history.melt(id_vars=['Stage'], var_name='Dimension', value_name='Score')
        fig_line = px.line(df_melted, x='Stage', y='Score', color='Dimension', markers=True)
        fig_line.update_layout(title="跨学期能力增长曲线")
        st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("3. AI 辅助评价 (System Feedback)")
    best_dim = max(latest_scores, key=lambda k: latest_scores[k] if k != 'Stage' else 0)
    worst_dim = min(latest_scores, key=lambda k: latest_scores[k] if k != 'Stage' else 100)
    
    st.success(f"✅ **能力亮点**：你在 **{best_dim}** 维度表现卓越，这与你简历中多次提到的项目经历高度契合。")
    st.info(f"💡 **提升建议**：检测到 **{worst_dim}** 是目前的相对弱项。建议结合 AI Copilot 搜索相关课程资料进行针对性强化。")

# --- 模块三：AI 教学 Copilot ---
def render_copilot():
    st.header("🤖 AI 教学助教 (Teaching Copilot)")
    st.caption("内置《新闻学概论》、《传播学教程》及大厂 JD 知识库")
    
    col_chat, col_context = st.columns([2, 1])
    
    with col_context:
        st.subheader("📚 推荐学习资源")
        st.markdown(f"""
        根据你的简历短板，为你推荐：
        
        **📖 阅读**
        - 《精确新闻报道》 (Philip Meyer) - *针对数据分析能力*
        - 普利策奖非虚构写作特稿选 - *针对叙事能力* 
        
        **▶️ 课程**
        - [Coursera] Python for Data Science
        - [Bilibili] 财新视频部：如何做短视频叙事
        """ 
        )
        
        st.info("💡 **提问提示**：\n- '如何用 STAR 法则优化我的实习经历？'\n- '什么是倒金字塔结构？'\n- '做数据新闻需要学什么？'")

    with col_chat:
        # 显示历史消息
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # 输入框
        if prompt := st.chat_input("向 AI 助教提问..."):
            # 用户消息
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # AI 回复
            with st.chat_message("assistant"):
                response_text = query_rag_knowledge_base(prompt)
                st.markdown(response_text)
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})

# --- 主程序入口 ---
def main():
    st.title("🎓 汕大新闻学院 | AI 赋能教学实验平台")
    
    tab1, tab2, tab3 = st.tabs(["🛠️ 智能简历工坊", "📊 成长数字孪生", "🤖 AI 教学 Copilot"])
    
    with tab1:
        render_resume_builder()
    
    with tab2:
        render_digital_twin()
        
    with tab3:
        render_copilot()

if __name__ == "__main__":
    main()