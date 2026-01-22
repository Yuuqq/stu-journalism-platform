"""
用户管理模块
提供简单的用户注册、登录和会话管理功能

Features:
- 基于学号/工号的简单认证
- 用户数据持久化到 JSON 文件
- 会话状态管理
- 支持 Streamlit Cloud 部署
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict, field

from .config import get_config

logger = logging.getLogger(__name__)


@dataclass
class User:
    """用户数据结构"""
    user_id: str                          # 学号/工号
    name: str                             # 姓名
    major: str = "journalism"             # 专业
    role: str = "student"                 # 角色: student, teacher, admin
    created_at: str = ""                  # 创建时间
    last_login: str = ""                  # 最后登录时间
    login_count: int = 0                  # 登录次数
    resume_versions: List[str] = field(default_factory=list)  # 简历版本列表

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class UserSession:
    """用户会话"""
    user: User
    login_time: str = ""
    is_authenticated: bool = False

    def __post_init__(self):
        if not self.login_time:
            self.login_time = datetime.now().isoformat()


class UserManager:
    """
    用户管理器
    负责用户注册、登录、会话管理
    """

    USERS_FILE = "users.json"

    def __init__(self):
        self.config = get_config()
        self._users_path = self.config.paths.data / self.USERS_FILE
        self._users: Dict[str, Dict] = {}
        self._load_users()

    def _load_users(self) -> None:
        """加载用户数据"""
        if self._users_path.exists():
            try:
                with open(self._users_path, 'r', encoding='utf-8') as f:
                    self._users = json.load(f)
                logger.info(f"Loaded {len(self._users)} users")
            except Exception as e:
                logger.error(f"Failed to load users: {e}")
                self._users = {}
        else:
            self._users = {}

    def _save_users(self) -> bool:
        """保存用户数据"""
        try:
            self._users_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._users_path, 'w', encoding='utf-8') as f:
                json.dump(self._users, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
            return False

    def _hash_password(self, password: str) -> str:
        """简单密码哈希（生产环境应使用 bcrypt）"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _validate_user_id(self, user_id: str) -> bool:
        """验证用户ID格式（学号/工号）"""
        # 允许字母、数字、下划线，长度 3-20
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, user_id))

    def register(
        self,
        user_id: str,
        name: str,
        password: str,
        major: str = "journalism",
        role: str = "student"
    ) -> tuple[bool, str]:
        """
        用户注册

        Args:
            user_id: 学号/工号
            name: 姓名
            password: 密码
            major: 专业
            role: 角色

        Returns:
            (是否成功, 消息)
        """
        # 验证用户ID
        if not self._validate_user_id(user_id):
            return False, "用户ID格式无效（3-20位字母、数字或下划线）"

        # 检查是否已存在
        if user_id in self._users:
            return False, "该用户ID已被注册"

        # 验证姓名
        name = name.strip()
        if len(name) < 2:
            return False, "姓名至少2个字符"

        # 验证密码
        if len(password) < 4:
            return False, "密码至少4位"

        # 创建用户
        user = User(
            user_id=user_id,
            name=name,
            major=major,
            role=role
        )

        # 保存
        self._users[user_id] = {
            **asdict(user),
            "password_hash": self._hash_password(password)
        }

        if self._save_users():
            logger.info(f"User registered: {user_id}")
            return True, "注册成功！"
        else:
            return False, "保存失败，请重试"

    def login(self, user_id: str, password: str) -> tuple[Optional[UserSession], str]:
        """
        用户登录

        Args:
            user_id: 学号/工号
            password: 密码

        Returns:
            (会话对象, 消息)
        """
        if user_id not in self._users:
            return None, "用户不存在"

        user_data = self._users[user_id]

        # 验证密码
        if user_data.get("password_hash") != self._hash_password(password):
            return None, "密码错误"

        # 更新登录信息
        user_data["last_login"] = datetime.now().isoformat()
        user_data["login_count"] = user_data.get("login_count", 0) + 1
        self._save_users()

        # 创建会话
        user = User(
            user_id=user_data["user_id"],
            name=user_data["name"],
            major=user_data.get("major", "journalism"),
            role=user_data.get("role", "student"),
            created_at=user_data.get("created_at", ""),
            last_login=user_data.get("last_login", ""),
            login_count=user_data.get("login_count", 0),
            resume_versions=user_data.get("resume_versions", [])
        )

        session = UserSession(user=user, is_authenticated=True)
        logger.info(f"User logged in: {user_id}")
        return session, "登录成功！"

    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户信息"""
        if user_id not in self._users:
            return None

        user_data = self._users[user_id]
        return User(
            user_id=user_data["user_id"],
            name=user_data["name"],
            major=user_data.get("major", "journalism"),
            role=user_data.get("role", "student"),
            created_at=user_data.get("created_at", ""),
            last_login=user_data.get("last_login", ""),
            login_count=user_data.get("login_count", 0),
            resume_versions=user_data.get("resume_versions", [])
        )

    def update_user_resume_versions(self, user_id: str, version: str) -> bool:
        """更新用户的简历版本列表"""
        if user_id not in self._users:
            return False

        versions = self._users[user_id].get("resume_versions", [])
        if version not in versions:
            versions.append(version)
            self._users[user_id]["resume_versions"] = versions
            return self._save_users()
        return True

    def get_all_users(self) -> List[Dict]:
        """获取所有用户（管理员功能）"""
        return [
            {
                "user_id": uid,
                "name": data.get("name", ""),
                "major": data.get("major", ""),
                "role": data.get("role", "student"),
                "login_count": data.get("login_count", 0),
                "last_login": data.get("last_login", ""),
                "resume_count": len(data.get("resume_versions", []))
            }
            for uid, data in self._users.items()
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """获取用户统计数据"""
        total_users = len(self._users)
        total_resumes = sum(
            len(data.get("resume_versions", []))
            for data in self._users.values()
        )

        # 按专业统计
        major_counts = {}
        for data in self._users.values():
            major = data.get("major", "journalism")
            major_counts[major] = major_counts.get(major, 0) + 1

        # 今日活跃用户
        today = datetime.now().date().isoformat()
        active_today = sum(
            1 for data in self._users.values()
            if data.get("last_login", "").startswith(today)
        )

        return {
            "total_users": total_users,
            "total_resumes": total_resumes,
            "major_distribution": major_counts,
            "active_today": active_today
        }


# 全局用户管理器实例
_user_manager: Optional[UserManager] = None


def get_user_manager() -> UserManager:
    """获取全局用户管理器实例"""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager
