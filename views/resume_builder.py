"""
智能简历工坊页面

提供简历编辑、预览和导出功能。
支持两种输入模式：
1. AI 智能提炼模式 - 学生用自然语言描述，AI 自动生成结构化简历
2. JSON 编辑模式 - 直接编辑 JSON 数据
"""
from __future__ import annotations

import json
import re
from typing import Dict, Any

import streamlit as st
from jinja2 import Template

from core.config import get_config
from core.data_manager import get_data_manager
from core.ai_service import extract_resume_from_text, AIServiceError


def _sanitize_student_id(student_id: str) -> str:
    """清理学生 ID，只允许字母、数字和下划线"""
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', student_id)
    return sanitized[:50]


def _validate_json_data(data: Dict[str, Any]) -> bool:
    """验证 JSON 数据结构"""
    if not isinstance(data, dict):
        return False
    json_str = json.dumps(data)
    if len(json_str) > 100000:
        return False
    return True


def render_resume_builder() -> None:
    """渲染简历生成器页面"""
    st.header("📝 智能简历工坊")

    config = get_config()
    data_mgr = get_data_manager()

    # 初始化简历数据
    if 'cv_data' not in st.session_state:
        st.session_state.cv_data = data_mgr.get_default_cv_config()

    # 输入模式选择
    input_mode = st.radio(
        "选择输入方式",
        ["🤖 AI 智能提炼", "📝 JSON 编辑器"],
        horizontal=True,
        key="res_input_mode",
        help="AI 智能提炼：用自然语言描述你的经历，AI 自动生成简历；JSON 编辑器：直接编辑结构化数据"
    )

    if input_mode == "🤖 AI 智能提炼":
        _render_ai_input_mode(config, data_mgr)
    else:
        _render_json_editor_mode(config, data_mgr)


def _render_ai_input_mode(config, data_mgr) -> None:
    """渲染 AI 智能提炼输入模式"""

    # ==================== 上半部分：AI 智能提炼输入 ====================
    st.subheader("✨ AI 智能提炼")

    # 第一行：三个按钮（横向对齐）
    col1, col2, col3 = st.columns(3)

    with col1:
        style_btn = st.button("🎨 风格配置", use_container_width=True, help="设置专业方向、排版布局、配色主题")

    with col2:
        save_btn = st.button("💾 保存存档", use_container_width=True, help="保存简历版本")

    with col3:
        help_btn = st.button("💡 输入示例", use_container_width=True, help="查看输入示例")

    # 根据按钮状态显示对应面板
    if "show_panel" not in st.session_state:
        st.session_state.show_panel = None

    if style_btn:
        st.session_state.show_panel = "style" if st.session_state.show_panel != "style" else None
    if save_btn:
        st.session_state.show_panel = "save" if st.session_state.show_panel != "save" else None
    if help_btn:
        st.session_state.show_panel = "help" if st.session_state.show_panel != "help" else None

    # 显示选中的面板
    if st.session_state.show_panel == "style":
        with st.container():
            st.markdown("##### 🎨 简历风格配置")
            _render_style_config(config)
            st.markdown("---")

    elif st.session_state.show_panel == "save":
        with st.container():
            st.markdown("##### 💾 保存版本存档")
            _render_save_section(data_mgr)
            st.markdown("---")

    elif st.session_state.show_panel == "help":
        with st.container():
            st.markdown("""
##### 💡 输入示例

你可以这样描述自己：

> 我叫张三，是汕头大学新闻学院大三学生，想找新闻记者的实习。
> 我的手机是 13800138000，邮箱 zhangsan@example.com。
>
> 我在校报工作了两年，采访了 50 多位师生，写了 30 篇稿子。
> 暑假在南方都市报实习，跟着记者老师跑了 10 个突发新闻现场。
>
> 我会用 Python 做数据分析，还会 Premiere 剪视频。英语过了六级。
>
> 获得过校级优秀学生记者、新闻写作比赛二等奖。
            """)
            st.markdown("---")

    # 获取当前选中的专业（从风格配置中）
    major_options = list(config.ui.major_presets.keys())
    selected_major = st.session_state.get("res_major_style", major_options[0])

    # 自然语言输入框
    user_input = st.text_area(
        "请描述你的个人信息、教育背景、实习经历、技能和获奖情况",
        height=200,
        placeholder="我叫..., 我是...专业的学生...\n\n我曾经在...实习/工作，主要负责...\n\n我会使用...，获得过...",
        key="ai_user_input"
    )

    # 生成按钮
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
    with col_btn1:
        generate_btn = st.button("🚀 AI 生成简历", type="primary", use_container_width=True)
    with col_btn2:
        clear_btn = st.button("🗑️ 清空重写", use_container_width=True)
    with col_btn3:
        pass  # 留白

    if clear_btn:
        st.session_state.cv_data = data_mgr.get_default_cv_config()
        st.rerun()

    if generate_btn and user_input.strip():
        # 创建进度显示容器
        progress_container = st.container()

        with progress_container:
            # 进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            log_container = st.empty()

            logs = []

            def update_log(message: str, progress: int):
                """更新日志和进度"""
                import time
                logs.append(f"[{time.strftime('%H:%M:%S')}] {message}")
                progress_bar.progress(progress)
                status_text.markdown(f"**{message}**")
                log_container.code("\n".join(logs[-5:]), language=None)

            try:
                update_log("📝 正在解析输入内容...", 10)

                # 获取配置
                major_key = _get_major_key(selected_major)
                input_length = len(user_input)
                update_log(f"📊 输入文本长度: {input_length} 字符", 20)

                update_log(f"🎯 专业方向: {selected_major}", 30)

                update_log("🔗 正在连接 AI 服务...", 40)

                # 导入并获取配置信息
                from core.ai_service import get_ai_config
                ai_config = get_ai_config()
                update_log(f"🤖 模型: {ai_config.model}", 50)
                update_log(f"🌐 API: {ai_config.base_url[:30]}...", 55)

                update_log("⏳ 正在调用 AI 分析内容（请稍候）...", 60)

                # 调用 AI 服务提取简历数据
                extracted_data = extract_resume_from_text(user_input, major_key)

                update_log("✨ AI 响应成功，正在解析结果...", 80)

                # 统计提取结果
                profile = extracted_data.get('profile', {})
                edu_count = len(extracted_data.get('education', []))
                exp_count = len(extracted_data.get('experience', []))
                skill_count = sum(len(v) for v in extracted_data.get('skills', {}).values() if isinstance(v, list))
                award_count = len(extracted_data.get('awards', []))

                update_log(f"👤 提取到个人信息: {profile.get('name', '未知')}", 85)
                update_log(f"🎓 教育经历: {edu_count} 条", 88)
                update_log(f"💼 工作/实习经历: {exp_count} 条", 91)
                update_log(f"🛠️ 技能: {skill_count} 项", 94)
                update_log(f"🏆 获奖: {award_count} 项", 97)

                update_log("✅ 简历生成完成！", 100)

                # 更新 session state
                st.session_state.cv_data = extracted_data

                # 清除进度显示
                import time
                time.sleep(0.5)
                progress_container.empty()

                st.success("✅ 简历生成成功！请查看下方预览效果。")
                st.balloons()
                st.rerun()

            except AIServiceError as e:
                update_log(f"❌ AI 服务错误: {str(e)}", 100)
                progress_bar.empty()
                st.error(f"AI 提炼失败：{str(e)}")
            except Exception as e:
                update_log(f"❌ 发生异常: {str(e)}", 100)
                progress_bar.empty()
                st.error(f"发生错误：{str(e)}")

    elif generate_btn:
        st.warning("请先输入你的个人描述")

    # ==================== 下半部分：实时预览 ====================
    st.markdown("---")
    _render_preview_section(config, data_mgr)


def _render_json_editor_mode(config, data_mgr) -> None:
    """渲染 JSON 编辑器模式"""

    st.subheader("📝 JSON 编辑器")

    # 第一行：三个按钮（与 AI 模式一致）
    col1, col2, col3 = st.columns(3)

    with col1:
        style_btn = st.button("🎨 风格配置", use_container_width=True, key="json_style_btn")

    with col2:
        load_btn = st.button("📂 加载示例", use_container_width=True, key="json_load_btn")

    with col3:
        save_btn = st.button("💾 保存存档", use_container_width=True, key="json_save_btn")

    # 面板状态
    if "json_panel" not in st.session_state:
        st.session_state.json_panel = None

    if style_btn:
        st.session_state.json_panel = "style" if st.session_state.json_panel != "style" else None
    if load_btn:
        st.session_state.json_panel = "load" if st.session_state.json_panel != "load" else None
    if save_btn:
        st.session_state.json_panel = "save" if st.session_state.json_panel != "save" else None

    # 显示面板
    if st.session_state.json_panel == "style":
        with st.container():
            st.markdown("##### 🎨 简历风格配置")
            _render_style_config(config)
            st.markdown("---")

    elif st.session_state.json_panel == "load":
        with st.container():
            st.markdown("##### 📂 加载示例数据")
            demo_configs = data_mgr.get_available_cv_configs()
            col_select, col_btn = st.columns([3, 1])

            with col_select:
                demo_choice = st.selectbox(
                    "选择示例",
                    list(demo_configs.keys()),
                    key="res_demo",
                    label_visibility="collapsed"
                )

            with col_btn:
                if st.button("加载", type="primary", key="res_load_btn", use_container_width=True):
                    config_name = demo_configs[demo_choice]
                    loaded_data = data_mgr.load_cv_config(config_name)
                    if loaded_data:
                        st.session_state.cv_data = loaded_data
                        st.success(f"已加载: {demo_choice}")
                        st.rerun()
            st.markdown("---")

    elif st.session_state.json_panel == "save":
        with st.container():
            st.markdown("##### 💾 保存版本存档")
            _render_save_section(data_mgr)
            st.markdown("---")

    # JSON 编辑器（左）和 预览（右）
    col_editor, col_preview = st.columns([1, 1])

    with col_editor:
        st.markdown("**数据编辑**")
        st.caption("直接编辑 JSON 数据，修改后自动同步到预览")

        edited_data_str = st.text_area(
            "JSON",
            value=json.dumps(st.session_state.cv_data, indent=2, ensure_ascii=False),
            height=500,
            key="res_json_editor",
            label_visibility="collapsed"
        )

        # 验证并更新
        try:
            current_data = json.loads(edited_data_str)
            st.session_state.cv_data = current_data
            st.success("✓ JSON 格式正确", icon="✅")
        except json.JSONDecodeError as e:
            st.error(f"JSON 格式错误: {str(e)}")

        # 格式化按钮
        if st.button("🔧 格式化 JSON", use_container_width=True):
            try:
                formatted = json.dumps(json.loads(edited_data_str), indent=2, ensure_ascii=False)
                st.session_state.cv_data = json.loads(formatted)
                st.rerun()
            except json.JSONDecodeError:
                st.error("无法格式化：JSON 格式错误")

    with col_preview:
        st.markdown("**实时预览**")

        # 获取样式配置
        style = st.session_state.get('cv_style', {
            'layout': 'classic',
            'theme_color': '#2563eb',
            'font_family': 'sans'
        })

        current_data = st.session_state.cv_data
        current_data['meta'] = style

        # 加载并渲染模板
        template_content = data_mgr.load_template(style['layout'])
        template = Template(template_content)
        html_output = template.render(**current_data)

        # 下载按钮
        st.download_button(
            "📥 下载简历 (HTML)",
            html_output,
            file_name="resume.html",
            mime="text/html",
            type="primary",
            use_container_width=True
        )

        # 预览
        st.components.v1.html(html_output, height=500, scrolling=True)


def _render_style_config(config) -> None:
    """渲染风格配置"""
    major_options = list(config.ui.major_presets.keys())

    if "res_major" not in st.session_state:
        st.session_state.res_major = major_options[0]

    major_preset = st.selectbox(
        "选择专业 (自动推荐风格)",
        major_options,
        key="res_major_style"
    )

    defaults = config.ui.major_presets[major_preset]

    layout = st.selectbox(
        "排版布局",
        config.ui.layouts,
        index=config.ui.layouts.index(defaults['layout']),
        key="res_layout"
    )

    theme_color = st.selectbox(
        "配色主题",
        config.ui.themes,
        index=config.ui.themes.index(defaults['theme']),
        key="res_theme"
    )

    font_options = ["sans", "serif"]
    font_family = st.radio(
        "字体风格",
        font_options,
        index=font_options.index(defaults['font']),
        key="res_font"
    )

    # 存储样式配置到 session state
    st.session_state.cv_style = {
        'layout': layout,
        'theme_color': theme_color,
        'font_family': font_family
    }


def _render_save_section(data_mgr) -> None:
    """渲染保存功能区"""
    st.caption("将当前简历保存为新版本，以生成成长轨迹。")
    save_id = st.text_input(
        "学生ID (英文)",
        value="my_cv",
        help="建议使用拼音，如 'zhang_san'",
        key="save_student_id"
    )

    if st.button("保存为新版本", type="primary", key="res_save_btn"):
        sanitized_id = _sanitize_student_id(save_id)
        if not sanitized_id:
            st.warning("请输入有效的学生ID（仅支持字母、数字和下划线）")
        else:
            try:
                data_to_save = st.session_state.cv_data

                if not _validate_json_data(data_to_save):
                    st.error("数据格式无效或数据过大")
                else:
                    new_ver = data_mgr.save_student_version(sanitized_id, data_to_save)

                    if new_ver:
                        st.success(f"✅ 保存成功！")
                        st.markdown(f"**档案**: `{sanitized_id}`\n**版本**: `{new_ver}`")
                        st.info("👉 请前往 [数字孪生] 页面查看您的成长轨迹演进。")
                    else:
                        st.error("保存失败，请检查日志")
            except Exception as e:
                st.error(f"发生错误: {str(e)}")


def _render_preview_section(config, data_mgr) -> None:
    """渲染预览区域"""
    st.subheader("👁️ 实时预览")

    current_data = st.session_state.cv_data

    # 获取样式配置
    style = st.session_state.get('cv_style', {
        'layout': 'classic',
        'theme_color': '#2563eb',
        'font_family': 'sans'
    })

    # 注入 Meta 配置
    current_data['meta'] = style

    # 加载并渲染模板
    template_content = data_mgr.load_template(style['layout'])
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

    # ==================== 简历参数修改 ====================
    st.markdown("---")
    st.subheader("✏️ 简历内容编辑")
    st.caption("直接修改下方内容，预览将实时更新")

    # 个人信息
    with st.expander("👤 个人信息", expanded=False):
        profile = current_data.get('profile', {})
        col1, col2 = st.columns(2)

        with col1:
            new_name = st.text_input("姓名", value=profile.get('name', ''), key="edit_name")
            new_phone = st.text_input("手机", value=profile.get('phone', ''), key="edit_phone")
            new_email = st.text_input("邮箱", value=profile.get('email', ''), key="edit_email")

        with col2:
            new_title = st.text_input("求职意向", value=profile.get('title', ''), key="edit_title")
            new_wechat = st.text_input("微信", value=profile.get('wechat', ''), key="edit_wechat")
            new_location = st.text_input("期望地点", value=profile.get('location', ''), key="edit_location")

        # 更新数据
        st.session_state.cv_data['profile'] = {
            **profile,
            'name': new_name,
            'phone': new_phone,
            'email': new_email,
            'title': new_title,
            'wechat': new_wechat,
            'location': new_location
        }

    # 教育经历
    with st.expander("🎓 教育经历", expanded=False):
        education_list = current_data.get('education', [])

        for i, edu in enumerate(education_list):
            st.markdown(f"**教育经历 {i+1}**")
            col1, col2 = st.columns(2)

            with col1:
                new_school = st.text_input("学校", value=edu.get('school', ''), key=f"edit_school_{i}")
                new_degree = st.text_input("专业/学位", value=edu.get('degree', ''), key=f"edit_degree_{i}")

            with col2:
                new_time = st.text_input("时间", value=edu.get('time', ''), key=f"edit_edu_time_{i}")

            # 详情列表
            details = edu.get('details', [])
            new_details = st.text_area(
                "详情（每行一条）",
                value="\n".join(details) if details else "",
                key=f"edit_edu_details_{i}",
                height=100
            )

            # 更新数据
            st.session_state.cv_data['education'][i] = {
                'school': new_school,
                'degree': new_degree,
                'time': new_time,
                'details': [d.strip() for d in new_details.split('\n') if d.strip()]
            }

            if i < len(education_list) - 1:
                st.markdown("---")

    # 工作/实习经历
    with st.expander("💼 工作/实习经历", expanded=False):
        experience_list = current_data.get('experience', [])

        if not experience_list:
            st.info("暂无工作经历，点击下方按钮添加")

        for i, exp in enumerate(experience_list):
            st.markdown(f"**经历 {i+1}**")
            col1, col2 = st.columns(2)

            with col1:
                new_company = st.text_input("公司/组织", value=exp.get('company', ''), key=f"edit_company_{i}")
                new_role = st.text_input("职位", value=exp.get('role', ''), key=f"edit_role_{i}")

            with col2:
                new_time = st.text_input("时间", value=exp.get('time', ''), key=f"edit_exp_time_{i}")

            details = exp.get('details', [])
            new_details = st.text_area(
                "工作成果（每行一条，建议用 STAR 法则）",
                value="\n".join(details) if details else "",
                key=f"edit_exp_details_{i}",
                height=100
            )

            st.session_state.cv_data['experience'][i] = {
                'company': new_company,
                'role': new_role,
                'time': new_time,
                'details': [d.strip() for d in new_details.split('\n') if d.strip()]
            }

            # 删除按钮
            if st.button(f"🗑️ 删除经历 {i+1}", key=f"del_exp_{i}"):
                st.session_state.cv_data['experience'].pop(i)
                st.rerun()

            if i < len(experience_list) - 1:
                st.markdown("---")

        # 添加新经历
        if st.button("➕ 添加工作经历", key="add_exp"):
            st.session_state.cv_data.setdefault('experience', []).append({
                'company': '待填写',
                'role': '待填写',
                'time': '待填写',
                'details': ['待填写']
            })
            st.rerun()

    # 技能
    with st.expander("🛠️ 技能", expanded=False):
        skills = current_data.get('skills', {})

        professional = st.text_area(
            "专业技能（每行一项）",
            value="\n".join(skills.get('professional', [])),
            key="edit_skills_pro",
            height=80
        )

        software = st.text_area(
            "软件工具（每行一项）",
            value="\n".join(skills.get('software', [])),
            key="edit_skills_soft",
            height=80
        )

        languages = st.text_area(
            "语言能力（每行一项）",
            value="\n".join(skills.get('languages', [])),
            key="edit_skills_lang",
            height=80
        )

        st.session_state.cv_data['skills'] = {
            'professional': [s.strip() for s in professional.split('\n') if s.strip()],
            'software': [s.strip() for s in software.split('\n') if s.strip()],
            'languages': [s.strip() for s in languages.split('\n') if s.strip()]
        }

    # 获奖情况
    with st.expander("🏆 获奖情况", expanded=False):
        awards = current_data.get('awards', [])

        new_awards = st.text_area(
            "获奖列表（每行一项）",
            value="\n".join(awards) if awards else "",
            key="edit_awards",
            height=100
        )

        st.session_state.cv_data['awards'] = [a.strip() for a in new_awards.split('\n') if a.strip()]

    # 作品集
    with st.expander("📂 作品集", expanded=False):
        portfolio_list = current_data.get('portfolio', [])

        if not portfolio_list:
            st.info("暂无作品，点击下方按钮添加")

        for i, work in enumerate(portfolio_list):
            st.markdown(f"**作品 {i+1}**")
            col1, col2 = st.columns(2)

            with col1:
                new_title = st.text_input("作品名称", value=work.get('title', ''), key=f"edit_work_title_{i}")
                new_role = st.text_input("你的角色", value=work.get('role', ''), key=f"edit_work_role_{i}")

            with col2:
                new_link = st.text_input("作品链接", value=work.get('link', ''), key=f"edit_work_link_{i}")
                new_desc = st.text_input("简短描述", value=work.get('desc', ''), key=f"edit_work_desc_{i}")

            st.session_state.cv_data['portfolio'][i] = {
                'title': new_title,
                'role': new_role,
                'link': new_link,
                'desc': new_desc
            }

            if st.button(f"🗑️ 删除作品 {i+1}", key=f"del_work_{i}"):
                st.session_state.cv_data['portfolio'].pop(i)
                st.rerun()

            if i < len(portfolio_list) - 1:
                st.markdown("---")

        if st.button("➕ 添加作品", key="add_work"):
            st.session_state.cv_data.setdefault('portfolio', []).append({
                'title': '待填写',
                'role': '待填写',
                'link': '',
                'desc': '待填写'
            })
            st.rerun()


def _get_major_key(major_display_name: str) -> str:
    """将显示名称转换为专业 key"""
    major_map = {
        "新闻学": "journalism",
        "广告学": "advertising",
        "网络与新媒体": "new_media",
        "广播电视学": "broadcasting"
    }
    return major_map.get(major_display_name, "journalism")
