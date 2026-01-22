"""
数据管理模块
统一处理简历数据、学生档案、能力评估等数据操作

该模块提供：
- StudentProfile: 学生档案数据结构
- DataManager: 数据管理器，负责所有数据的读写和转换
- get_data_manager: 获取全局数据管理器实例
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from functools import lru_cache

from .config import get_config

# 配置日志
logger = logging.getLogger(__name__)

# 缓存过期时间（秒）
CACHE_TTL = 300  # 5分钟


@dataclass
class CacheEntry:
    """缓存条目，包含数据和时间戳"""
    data: Any
    timestamp: float = field(default_factory=time.time)

    def is_expired(self, ttl: float = CACHE_TTL) -> bool:
        """检查缓存是否过期"""
        return time.time() - self.timestamp > ttl


@dataclass
class StudentProfile:
    """学生档案数据结构

    Attributes:
        id: 学生唯一标识符
        name: 学生姓名
        major: 专业（默认为 journalism）
        current_version: 当前版本号
        cv_data: 简历数据
        competency_scores: 能力评估分数
    """
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

    Features:
        - 带 TTL 的缓存机制
        - 线程安全的文件操作
        - 自动版本管理
    """

    def __init__(self):
        self.config = get_config()
        self._cv_cache: Dict[str, CacheEntry] = {}
        self._student_cache: Dict[str, CacheEntry] = {}

    def _get_from_cache(self, cache: Dict[str, CacheEntry], key: str) -> Optional[Dict]:
        """从缓存获取数据，如果过期则返回 None"""
        if key in cache:
            entry = cache[key]
            if not entry.is_expired():
                return entry.data.copy()
            del cache[key]
        return None

    def _set_cache(self, cache: Dict[str, CacheEntry], key: str, data: Dict) -> None:
        """设置缓存"""
        cache[key] = CacheEntry(data=data.copy())

    def clear_cache(self) -> None:
        """清除所有缓存"""
        self._cv_cache.clear()
        self._student_cache.clear()
        logger.info("Cache cleared")

    # ==================== 简历数据操作 ====================

    def load_cv_config(self, name: str) -> Dict:
        """
        加载简历配置

        Args:
            name: 配置名称 (advertising, journalism, new_media, broadcasting)

        Returns:
            简历配置字典
        """
        # 检查缓存
        cached = self._get_from_cache(self._cv_cache, name)
        if cached is not None:
            return cached

        path = self.config.get_cv_config_path(name)
        data = self._load_json(path)

        if data:
            self._set_cache(self._cv_cache, name, data)

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
        history = []
        student_dir = self.config.paths.students
        
        # 动态搜索所有版本：config_{student_id}_v*.json
        pattern = f"config_{student_id}_v*.json"
        files = list(student_dir.glob(pattern))
        
        # 按版本号排序 (v1, v2, v10)
        def version_key(path):
            try:
                filename = path.stem
                parts = filename.split('_')
                v_part = parts[-1]  # v1
                return int(v_part[1:])
            except (ValueError, IndexError):
                return 0
                
        files.sort(key=version_key)

        for path in files:
            data = self._load_json(path)
            if data:
                filename = path.stem
                parts = filename.split('_')
                version = parts[-1]
                
                data['_version'] = version
                history.append(data)

        return history

    def save_student_version(self, student_id: str, data: Dict) -> str:
        """
        保存为新版本
        自动计算 v{n+1}
        """
        student_dir = self.config.paths.students
        pattern = f"config_{student_id}_v*.json"
        files = list(student_dir.glob(pattern))
        
        max_version = 0
        for path in files:
            try:
                filename = path.stem
                parts = filename.split('_')
                v_part = parts[-1]
                v_num = int(v_part[1:])
                if v_num > max_version:
                    max_version = v_num
            except (ValueError, IndexError):
                pass
        
        next_version = f"v{max_version + 1}"
        filename = f"config_{student_id}_{next_version}.json"
        path = student_dir / filename
        
        # 确保保存版本信息
        data_to_save = data.copy()
        data_to_save['_version'] = next_version
        
        if self._save_json(path, data_to_save):
            # 清除缓存
            if student_id in self._student_cache:
                del self._student_cache[student_id]
            return next_version
        return ""

    def get_available_students(self) -> Dict[str, str]:
        """获取所有可用的学生档案"""
        students = {
            "current": "📝 当前编辑中 (实时分析)",
            "zhang": "Zhang X霸 (模拟-学霸型)",
            "li": "Li 导演 (模拟-特长型)",
            "wang": "Wang 逆袭 (模拟-进步型)"
        }
        
        # 动态扫描目录下的其他存档
        try:
            student_dir = self.config.paths.students
            if student_dir.exists():
                for path in student_dir.glob("config_*_v*.json"):
                    try:
                        filename = path.stem  # config_student_v1
                        parts = filename.split('_')
                        # 假设结构为 config_{id}_{version}
                        if len(parts) >= 3:
                            version_part = parts[-1]
                            if version_part.startswith('v') and version_part[1:].isdigit():
                                # 提取 ID (兼容带下划线的 ID)
                                s_id = "_".join(parts[1:-1])
                                
                                if s_id not in students:
                                    students[s_id] = f"{s_id} (存档记录)"
                    except Exception:
                        continue
        except Exception as e:
            print(f"Error scanning students: {e}")
            
        return students

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
        """安全加载 JSON 文件

        Args:
            path: 文件路径

        Returns:
            解析后的字典，失败时返回空字典
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.debug(f"File not found: {path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {path}: {e}")
            return {}

    def _save_json(self, path: Path, data: Dict) -> bool:
        """安全保存 JSON 文件

        Args:
            path: 文件路径
            data: 要保存的数据

        Returns:
            是否保存成功
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved: {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving {path}: {e}")
            return False


# 全局数据管理器实例
_data_manager: Optional[DataManager] = None

def get_data_manager() -> DataManager:
    """获取全局数据管理器实例"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager
