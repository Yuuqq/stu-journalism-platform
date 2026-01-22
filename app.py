"""
汕大新闻学院 AI 赋能教学实验平台
主应用入口
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.config import get_config
from views import render_resume_builder, render_digital_twin, render_ai_copilot


def init_app():
    """初始化应用配置"""
    config = get_config()

    st.set_page_config(
        layout=config.ui.layout,
        page_title=config.ui.page_title,
        page_icon=config.ui.page_icon
    )


def main():
    """主函数"""
    init_app()

    st.title("🎓 汕大新闻学院 | AI 赋能教学实验平台")

    # 三个标签页
    tab1, tab2, tab3 = st.tabs([
        "🛠️ 智能简历工坊",
        "📊 成长数字孪生",
        "🤖 AI 教学 Copilot"
    ])

    with tab1:
        render_resume_builder()

    with tab2:
        render_digital_twin()

    with tab3:
        render_ai_copilot()


if __name__ == "__main__":
    main()
