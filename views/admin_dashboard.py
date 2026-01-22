"""
数据统计与管理页面

为教师/管理员提供数据统计、用户管理和数据导出功能。
"""
from __future__ import annotations

import json
import csv
import io
from datetime import datetime
from typing import Dict, Any, List

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.user_manager import get_user_manager
from core.data_manager import get_data_manager
from core.config import get_config


def render_admin_dashboard() -> None:
    """渲染管理员仪表板"""
    st.header("📊 数据统计与管理")

    # 检查权限
    if "user_session" not in st.session_state:
        st.warning("请先登录")
        return

    session = st.session_state.user_session
    if session.user.role not in ["admin", "teacher"]:
        st.warning("此功能仅对教师和管理员开放")
        return

    # 获取管理器
    user_mgr = get_user_manager()
    data_mgr = get_data_manager()
    config = get_config()

    # 统计数据
    stats = user_mgr.get_statistics()

    # 顶部指标卡片
    _render_metrics(stats)

    st.markdown("---")

    # 两栏布局
    col1, col2 = st.columns([1, 1])

    with col1:
        _render_major_distribution(stats)

    with col2:
        _render_activity_chart(user_mgr)

    st.markdown("---")

    # 用户列表
    _render_user_list(user_mgr)

    st.markdown("---")

    # 数据导出
    _render_export_section(user_mgr, data_mgr)


def _render_metrics(stats: Dict[str, Any]) -> None:
    """渲染指标卡片"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="总注册用户",
            value=stats["total_users"],
            delta=None
        )

    with col2:
        st.metric(
            label="生成简历数",
            value=stats["total_resumes"],
            delta=None
        )

    with col3:
        st.metric(
            label="今日活跃",
            value=stats["active_today"],
            delta=None
        )

    with col4:
        avg_resumes = (
            stats["total_resumes"] / stats["total_users"]
            if stats["total_users"] > 0 else 0
        )
        st.metric(
            label="人均简历版本",
            value=f"{avg_resumes:.1f}",
            delta=None
        )


def _render_major_distribution(stats: Dict[str, Any]) -> None:
    """渲染专业分布饼图"""
    st.subheader("专业分布")

    major_dist = stats.get("major_distribution", {})

    if not major_dist:
        st.info("暂无数据")
        return

    # 专业名称映射
    major_names = {
        "journalism": "新闻学",
        "advertising": "广告学",
        "new_media": "网络与新媒体",
        "broadcasting": "广播电视学"
    }

    labels = [major_names.get(k, k) for k in major_dist.keys()]
    values = list(major_dist.values())

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4
    )])

    fig.update_layout(
        title="按专业分布",
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_activity_chart(user_mgr) -> None:
    """渲染活动趋势图"""
    st.subheader("用户活动")

    users = user_mgr.get_all_users()

    if not users:
        st.info("暂无数据")
        return

    # 按登录次数排序
    sorted_users = sorted(users, key=lambda x: x["login_count"], reverse=True)[:10]

    if sorted_users:
        df = pd.DataFrame(sorted_users)

        fig = px.bar(
            df,
            x="name",
            y="login_count",
            title="活跃用户 TOP 10",
            labels={"name": "用户", "login_count": "登录次数"}
        )

        st.plotly_chart(fig, use_container_width=True)


def _render_user_list(user_mgr) -> None:
    """渲染用户列表"""
    st.subheader("用户列表")

    users = user_mgr.get_all_users()

    if not users:
        st.info("暂无注册用户")
        return

    # 专业名称映射
    major_names = {
        "journalism": "新闻学",
        "advertising": "广告学",
        "new_media": "网络与新媒体",
        "broadcasting": "广播电视学"
    }

    # 构建数据
    table_data = []
    for user in users:
        table_data.append({
            "学号": user["user_id"],
            "姓名": user["name"],
            "专业": major_names.get(user["major"], user["major"]),
            "角色": user["role"],
            "登录次数": user["login_count"],
            "简历版本数": user["resume_count"],
            "最后登录": user["last_login"][:10] if user["last_login"] else "-"
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_export_section(user_mgr, data_mgr) -> None:
    """渲染数据导出功能"""
    st.subheader("数据导出")

    col1, col2, col3 = st.columns(3)

    with col1:
        # 导出用户数据
        if st.button("📥 导出用户数据 (CSV)", use_container_width=True):
            users = user_mgr.get_all_users()
            if users:
                csv_data = _export_users_csv(users)
                st.download_button(
                    "下载 users.csv",
                    csv_data,
                    file_name=f"users_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("暂无用户数据")

    with col2:
        # 导出统计报告
        if st.button("📊 导出统计报告 (JSON)", use_container_width=True):
            stats = user_mgr.get_statistics()
            report = _generate_report(stats, user_mgr)
            st.download_button(
                "下载 report.json",
                json.dumps(report, ensure_ascii=False, indent=2),
                file_name=f"report_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

    with col3:
        # 导出所有简历数据
        if st.button("📝 导出简历数据 (JSON)", use_container_width=True):
            resumes = _collect_all_resumes(data_mgr)
            if resumes:
                st.download_button(
                    "下载 resumes.json",
                    json.dumps(resumes, ensure_ascii=False, indent=2),
                    file_name=f"resumes_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            else:
                st.warning("暂无简历数据")


def _export_users_csv(users: List[Dict]) -> str:
    """导出用户数据为 CSV"""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "user_id", "name", "major", "role", "login_count", "resume_count", "last_login"
    ])
    writer.writeheader()
    for user in users:
        writer.writerow(user)
    return output.getvalue()


def _generate_report(stats: Dict, user_mgr) -> Dict:
    """生成统计报告"""
    return {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_users": stats["total_users"],
            "total_resumes": stats["total_resumes"],
            "active_today": stats["active_today"]
        },
        "major_distribution": stats["major_distribution"],
        "user_details": user_mgr.get_all_users()
    }


def _collect_all_resumes(data_mgr) -> List[Dict]:
    """收集所有简历数据"""
    config = get_config()
    resumes = []

    students_dir = config.paths.students
    if students_dir.exists():
        for path in students_dir.glob("config_*_v*.json"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data["_source_file"] = path.name
                    resumes.append(data)
            except Exception:
                continue

    return resumes
