"""
数据管理模块
统一处理简历数据、学生档案、能力评估等数据操作
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .config import get_config


@dataclass
class StudentProfile:
    """学生档案数据结构"""
    id: str
    name: str
    major: str = "journalism"
    current_version: str = "v1"
    cv_data: Optional[Dict] = None
    competency_scores: Optional[Dict] = None


class DataManager:
    """
    数据管理器
    负责所有数据的读写和转换
    """

    def __init__(self):
        self.config = get_config()
        self._cv_cache: Dict[str, Dict] = {}
        self._student_cache: Dict[str, Dict] = {}

    # ==================== 简历数据操作 ====================

    def load_cv_config(self, name: str) -> Dict:
        """
        加载简历配置
        name: advertising, journalism, new_media, broadcasting
        """
        if name in self._cv_cache:
            return self._cv_cache[name].copy()

        path = self.config.get_cv_config_path(name)
        data = self._load_json(path)

        if data:
            self._cv_cache[name] = data

        return data

    def get_default_cv_config(self) -> Dict:
        """获取默认简历配置"""
        return self.load_cv_config("advertising")

    def get_available_cv_configs(self) -> Dict[str, str]:
        """获取所有可用的简历配置"""
        return {
            "广告学示例": "advertising",
            "网新示例": "new_media",
            "新闻学示例": "journalism",
            "广电示例": "broadcasting"
        }

    # ==================== 学生档案操作 ====================

    def load_student_history(self, student_id: str) -> List[Dict]:
        """
        加载学生的历史版本数据
        返回按版本排序的数据列表
        """
        versions = ["v1", "v2", "v3"]
        history = []

        for version in versions:
            path = self.config.get_student_config_path(student_id, version)
            if path.exists():
                data = self._load_json(path)
                if data:
                    data['_version'] = version
                    history.append(data)

        return history

    def get_available_students(self) -> Dict[str, str]:
        """获取所有可用的学生档案"""
        return {
            "current": "📝 当前编辑中 (实时分析)",
            "zhang": "Zhang X霸 (模拟-学霸型)",
            "li": "Li 导演 (模拟-特长型)",
            "wang": "Wang 逆袭 (模拟-进步型)"
        }

    # ==================== 能力评估 ====================

    def calculate_competency_scores(
        self,
        cv_data: Dict,
        major: str = "journalism"
    ) -> Dict[str, float]:
        """
        基于简历内容计算能力维度得分

        算法：
        1. 将简历数据序列化为文本
        2. 对每个能力维度，统计关键词匹配数
        3. 基准分 + 关键词加成（每个关键词+5分，上限100）
        """
        matrix = self.config.competency_matrix
        major_config = matrix.get(major, matrix.get("journalism", {}))

        dimensions = major_config.get("dimensions", {})
        baseline = major_config.get("baseline_score", 60)

        # 序列化简历内容用于搜索
        text_blob = json.dumps(cv_data, ensure_ascii=False).lower()

        scores = {}
        for dim_id, dim_info in dimensions.items():
            label = dim_info.get("label", dim_id)
            keywords = dim_info.get("keywords", [])

            # 统计关键词匹配
            match_count = sum(1 for kw in keywords if kw.lower() in text_blob)

            # 计算得分
            score = baseline + (match_count * 5)
            scores[label] = min(score, 100)

        return scores

    def get_competency_feedback(
        self,
        scores: Dict[str, float]
    ) -> Dict[str, str]:
        """
        基于能力得分生成反馈建议
        """
        if not scores:
            return {"highlight": "", "suggestion": ""}

        # 过滤掉非数值字段（如 'Stage'）
        numeric_scores = {k: v for k, v in scores.items() if isinstance(v, (int, float))}

        if not numeric_scores:
            return {"highlight": "", "suggestion": ""}

        best_dim = max(numeric_scores, key=numeric_scores.get)
        worst_dim = min(numeric_scores, key=numeric_scores.get)

        return {
            "highlight": f"你在 **{best_dim}** 维度表现卓越，这与你简历中多次提到的项目经历高度契合。",
            "suggestion": f"检测到 **{worst_dim}** 是目前的相对弱项。建议结合 AI Copilot 搜索相关课程资料进行针对性强化。"
        }

    # ==================== 模板操作 ====================

    def load_template(self, layout: str) -> str:
        """加载 HTML 模板"""
        path = self.config.get_template_path(layout)

        # 如果找不到，回退到默认模板
        if not path.exists():
            path = self.config.get_template_path("modern")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading template {path}: {e}")
            return "<html><body><h1>Template Error</h1></body></html>"

    # ==================== 工具方法 ====================

    def _load_json(self, path: Path) -> Dict:
        """安全加载 JSON 文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            print(f"JSON decode error in {path}: {e}")
            return {}

    def _save_json(self, path: Path, data: Dict) -> bool:
        """安全保存 JSON 文件"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving {path}: {e}")
            return False


# 全局数据管理器实例
_data_manager: Optional[DataManager] = None

def get_data_manager() -> DataManager:
    """获取全局数据管理器实例"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager
