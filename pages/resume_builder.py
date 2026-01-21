"""
智能简历工坊页面
"""
import json
import streamlit as st
from jinja2 import Template

from core.config import get_config
from core.data_manager import get_data_manager


def render_resume_builder():
    """渲染简历生成器页面"""
    st.header("📝 智能简历工坊")

    config = get_config()
    data_mgr = get_data_manager()

    # 初始化简历数据
    if 'cv_data' not in st.session_state:
        st.session_state.cv_data = data_mgr.get_default_cv_config()

    # 三栏布局
    col_config, col_editor, col_preview = st.columns([1, 2, 2])

    # ==================== 左栏: 风格配置 ====================
    with col_config:
        st.subheader("🎨 风格配置")

        # 专业预设选择
        major_options = list(config.ui.major_presets.keys())
        major_preset = st.selectbox(
            "选择专业 (自动推荐风格)",
            major_options,
            key="res_major"
        )

        # 获取预设默认值
        defaults = config.ui.major_presets[major_preset]

        # 布局选择
        layout = st.selectbox(
            "排版布局",
            config.ui.layouts,
            index=config.ui.layouts.index(defaults['layout']),
            key="res_layout"
        )

        # 配色选择
        theme_color = st.selectbox(
            "配色主题",
            config.ui.themes,
            index=config.ui.themes.index(defaults['theme']),
            key="res_theme"
        )

        # 字体选择
        font_options = ["sans", "serif"]
        font_family = st.radio(
            "字体风格",
            font_options,
            index=font_options.index(defaults['font']),
            key="res_font"
        )

        st.markdown("---")

        # 加载示例数据
        with st.expander("📂 加载示例数据"):
            demo_configs = data_mgr.get_available_cv_configs()
            demo_choice = st.selectbox(
                "选择示例",
                ["当前数据"] + list(demo_configs.keys()),
                key="res_demo"
            )

            if st.button("加载数据", key="res_load_btn"):
                if demo_choice in demo_configs:
                    config_name = demo_configs[demo_choice]
                    loaded_data = data_mgr.load_cv_config(config_name)
                    if loaded_data:
                        st.session_state.cv_data = loaded_data
                        st.rerun()

    # ==================== 中栏: 数据编辑 ====================
    with col_editor:
        st.subheader("✏️ 数据编辑")

        edited_data_str = st.text_area(
            "JSON 编辑器",
            value=json.dumps(st.session_state.cv_data, indent=4, ensure_ascii=False),
            height=600,
            key="res_json_editor"
        )

        try:
            current_data = json.loads(edited_data_str)
            st.session_state.cv_data = current_data

            # 注入 Meta 配置
            current_data['meta'] = {
                'layout': layout,
                'theme_color': theme_color,
                'font_family': font_family
            }
        except json.JSONDecodeError:
            st.error("JSON 格式错误，请检查语法")
            current_data = st.session_state.cv_data

    # ==================== 右栏: 实时预览 ====================
    with col_preview:
        st.subheader("👁️ 实时预览")

        # 加载并渲染模板
        template_content = data_mgr.load_template(layout)
        template = Template(template_content)
        html_output = template.render(**current_data)

        # 下载按钮
        st.download_button(
            "📥 下载简历 (HTML)",
            html_output,
            file_name="resume.html",
            mime="text/html",
            type="primary"
        )

        # 预览
        st.components.v1.html(html_output, height=800, scrolling=True)
