"""
汕大新闻学院 AI 赋能教学实验平台
主应用入口

该平台提供三大功能模块：
1. 智能简历工坊 - 简历编辑和预览
2. 成长数字孪生 - 能力分析和可视化
3. AI 教学 Copilot - 基于 RAG 的智能问答

Features:
- 简单用户认证系统
- 多学生数据隔离
- 支持 Streamlit Cloud 部署
"""
import sys
import logging
from pathlib import Path
from typing import Callable

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.config import get_config
from core.user_manager import get_user_manager, UserSession
from views import render_resume_builder, render_digital_twin, render_ai_copilot, render_admin_dashboard

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def safe_render(render_func: Callable, tab_name: str) -> None:
    """安全渲染页面，捕获异常并显示友好错误信息"""
    try:
        render_func()
    except Exception as e:
        logger.exception(f"Error rendering {tab_name}")
        st.error(f"⚠️ 页面加载出错")
        st.markdown(f"""
        **错误信息**: `{str(e)}`

        **可能的解决方案**:
        - 刷新页面重试
        - 检查数据文件是否完整
        - 查看控制台日志获取详细信息
        """)


def init_app():
    """初始化应用配置"""
    config = get_config()

    st.set_page_config(
        layout=config.ui.layout,
        page_title=config.ui.page_title,
        page_icon=config.ui.page_icon
    )


def render_auth_sidebar() -> bool:
    """
    渲染侧边栏用户认证界面

    Returns:
        是否已登录
    """
    user_mgr = get_user_manager()

    with st.sidebar:
        st.markdown("### 👤 用户中心")

        # 检查登录状态
        if "user_session" in st.session_state and st.session_state.user_session:
            session: UserSession = st.session_state.user_session
            st.success(f"欢迎, **{session.user.name}**!")
            st.caption(f"学号: {session.user.user_id}")
            st.caption(f"专业: {session.user.major}")

            if st.button("退出登录", use_container_width=True):
                del st.session_state.user_session
                st.rerun()

            st.markdown("---")
            return True

        # 未登录：显示登录/注册表单
        auth_mode = st.radio(
            "选择操作",
            ["登录", "注册"],
            horizontal=True,
            key="auth_mode"
        )

        if auth_mode == "登录":
            _render_login_form(user_mgr)
        else:
            _render_register_form(user_mgr)

        st.markdown("---")

        # 游客模式
        st.caption("或者以游客身份体验：")
        if st.button("🎭 游客模式", use_container_width=True):
            # 创建临时游客会话
            from core.user_manager import User
            guest_user = User(
                user_id="guest",
                name="游客",
                major="journalism",
                role="guest"
            )
            st.session_state.user_session = UserSession(
                user=guest_user,
                is_authenticated=False
            )
            st.rerun()

        return False


def _render_login_form(user_mgr) -> None:
    """渲染登录表单"""
    with st.form("login_form"):
        user_id = st.text_input(
            "学号/工号",
            placeholder="请输入学号或工号",
            key="login_user_id"
        )
        password = st.text_input(
            "密码",
            type="password",
            placeholder="请输入密码",
            key="login_password"
        )

        submitted = st.form_submit_button("登录", use_container_width=True)

        if submitted:
            if not user_id or not password:
                st.error("请填写完整信息")
            else:
                session, msg = user_mgr.login(user_id, password)
                if session:
                    st.session_state.user_session = session
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


def _render_register_form(user_mgr) -> None:
    """渲染注册表单"""
    config = get_config()

    with st.form("register_form"):
        user_id = st.text_input(
            "学号/工号",
            placeholder="3-20位字母、数字或下划线",
            key="reg_user_id"
        )
        name = st.text_input(
            "姓名",
            placeholder="请输入真实姓名",
            key="reg_name"
        )
        major = st.selectbox(
            "专业",
            list(config.ui.major_presets.keys()),
            key="reg_major"
        )
        password = st.text_input(
            "密码",
            type="password",
            placeholder="至少4位",
            key="reg_password"
        )
        password2 = st.text_input(
            "确认密码",
            type="password",
            placeholder="再次输入密码",
            key="reg_password2"
        )

        submitted = st.form_submit_button("注册", use_container_width=True)

        if submitted:
            if not all([user_id, name, password, password2]):
                st.error("请填写完整信息")
            elif password != password2:
                st.error("两次密码不一致")
            else:
                # 转换专业名称
                major_key = _get_major_key(major)
                success, msg = user_mgr.register(user_id, name, password, major_key)
                if success:
                    st.success(msg + " 请登录")
                else:
                    st.error(msg)


def _get_major_key(major_display_name: str) -> str:
    """将显示名称转换为专业 key"""
    major_map = {
        "新闻学": "journalism",
        "广告学": "advertising",
        "网络与新媒体": "new_media",
        "广播电视学": "broadcasting"
    }
    return major_map.get(major_display_name, "journalism")


def render_admin_stats() -> None:
    """渲染管理员统计面板（侧边栏）"""
    if "user_session" not in st.session_state:
        return

    session = st.session_state.user_session
    if session.user.role not in ["admin", "teacher"]:
        return

    user_mgr = get_user_manager()
    stats = user_mgr.get_statistics()

    with st.sidebar:
        st.markdown("### 📊 数据统计")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("总用户", stats["total_users"])
        with col2:
            st.metric("总简历", stats["total_resumes"])

        st.caption(f"今日活跃: {stats['active_today']}")


def main():
    """主函数"""
    init_app()
    logger.info("Application started")

    # 用户认证
    is_logged_in = render_auth_sidebar()

    # 管理员统计
    render_admin_stats()

    # 主标题
    st.title("🎓 汕大新闻学院 | AI 赋能教学实验平台")

    # 检查是否有用户会话
    if "user_session" not in st.session_state:
        # 显示欢迎页面
        st.markdown("""
        ## 👋 欢迎使用 AI 赋能教学实验平台

        本平台为汕头大学新闻学院学生提供：

        - **🛠️ 智能简历工坊** - 用自然语言描述你的经历，AI 帮你生成专业简历
        - **📊 成长数字孪生** - 可视化你的能力发展轨迹
        - **🤖 AI 教学 Copilot** - 基于课程资料的智能问答助手

        👈 请在左侧 **登录** 或 **注册** 开始使用
        """)

        # 显示快速体验按钮
        st.info("💡 首次使用？可以点击左侧「游客模式」快速体验！")
        return

    # 已登录/游客：显示主功能
    session = st.session_state.user_session

    # 将用户信息存入 session_state 供其他模块使用
    st.session_state.current_user_id = session.user.user_id
    st.session_state.current_user_name = session.user.name
    st.session_state.current_user_major = session.user.major

    # 根据角色显示不同的标签页
    is_admin = session.user.role in ["admin", "teacher"]

    if is_admin:
        # 管理员/教师：显示四个标签页
        tab1, tab2, tab3, tab4 = st.tabs([
            "🛠️ 智能简历工坊",
            "📊 成长数字孪生",
            "🤖 AI 教学 Copilot",
            "📈 数据统计"
        ])
    else:
        # 学生/游客：显示三个标签页
        tab1, tab2, tab3 = st.tabs([
            "🛠️ 智能简历工坊",
            "📊 成长数字孪生",
            "🤖 AI 教学 Copilot"
        ])
        tab4 = None

    with tab1:
        safe_render(render_resume_builder, "智能简历工坊")

    with tab2:
        safe_render(render_digital_twin, "成长数字孪生")

    with tab3:
        safe_render(render_ai_copilot, "AI 教学 Copilot")

    if tab4:
        with tab4:
            safe_render(render_admin_dashboard, "数据统计")


if __name__ == "__main__":
    main()
