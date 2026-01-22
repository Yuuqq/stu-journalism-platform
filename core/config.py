"""
统一配置管理模块
集中管理所有路径、常量和系统设置

该模块提供：
- PathConfig: 路径配置，管理项目中所有文件路径
- UIConfig: UI 配置，管理界面相关设置
- RAGConfig: RAG 引擎配置
- Config: 全局配置管理器（单例模式）
"""
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# 配置日志
logger = logging.getLogger(__name__)

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent


@dataclass
class PathConfig:
    """路径配置"""
    root: Path = field(default_factory=lambda: ROOT_DIR)

    @property
    def templates(self) -> Path:
        return self.root / "templates"

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def students(self) -> Path:
        return self.data / "students"

    @property
    def corpus(self) -> Path:
        return self.root / "assets" / "corpus"

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def competency_matrix(self) -> Path:
        return self.config / "competency_matrix.json"

    @property
    def cv_configs(self) -> Path:
        return self.root / "journalism_cv"


@dataclass
class UIConfig:
    """UI 配置"""
    page_title: str = "汕大新闻学院数智化教学平台"
    page_icon: str = "🎓"
    layout: str = "wide"

    # 专业预设
    major_presets: Dict = field(default_factory=lambda: {
        "自定义": {"layout": "modern", "theme": "rose", "font": "sans"},
        "广告学 (Agency)": {"layout": "agency", "theme": "luxury", "font": "sans"},
        "新闻学 (Classic)": {"layout": "classic", "theme": "academic", "font": "serif"},
        "网新 (Modern)": {"layout": "modern", "theme": "teal", "font": "sans"},
        "广播电视 (Visual)": {"layout": "visual", "theme": "violet", "font": "sans"}
    })

    # 模板映射
    template_map: Dict = field(default_factory=lambda: {
        "modern": "template.html",
        "classic": "template_classic.html",
        "agency": "template_agency.html",
        "visual": "template_visual.html"
    })

    # 配色主题
    themes: List[str] = field(default_factory=lambda: [
        "rose", "teal", "indigo", "violet", "academic", "luxury"
    ])

    # 布局选项
    layouts: List[str] = field(default_factory=lambda: [
        "modern", "classic", "agency", "visual"
    ])


@dataclass
class RAGConfig:
    """RAG 引擎配置

    Attributes:
        chunk_size: 文本分块大小（字符数）
        chunk_overlap: 分块重叠大小
        min_chunk_length: 最小分块长度
        ngram_range: N-gram 范围，用于中文字符级匹配
        similarity_threshold: 相似度阈值
        top_k: 返回的最相关结果数量
    """
    chunk_size: int = 200
    chunk_overlap: int = 40
    min_chunk_length: int = 10
    ngram_range: Tuple[int, int] = (2, 4)
    similarity_threshold: float = 0.02
    top_k: int = 2


class Config:
    """
    全局配置管理器
    单例模式，确保全局只有一个配置实例
    """
    _instance: Optional['Config'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.paths = PathConfig()
        self.ui = UIConfig()
        self.rag = RAGConfig()

        # 加载能力矩阵配置
        self._competency_matrix: Optional[Dict] = None

        self._initialized = True

    @property
    def competency_matrix(self) -> Dict:
        """延迟加载能力矩阵配置"""
        if self._competency_matrix is None:
            self._competency_matrix = self._load_json(self.paths.competency_matrix)
        return self._competency_matrix

    def _load_json(self, path: Path) -> Dict:
        """安全加载 JSON 文件

        Args:
            path: JSON 文件路径

        Returns:
            解析后的字典，如果加载失败返回空字典
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {path}")
            return {}
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {path}: {e}")
            return {}

    def get_cv_config_path(self, name: str) -> Path:
        """获取简历配置文件路径"""
        return self.paths.cv_configs / f"config_{name}.json"

    def get_student_config_path(self, student_id: str, version: str) -> Path:
        """获取学生档案路径"""
        return self.paths.students / f"config_{student_id}_{version}.json"

    def get_template_path(self, layout: str) -> Path:
        """获取模板文件路径"""
        filename = self.ui.template_map.get(layout, "template.html")
        return self.paths.cv_configs / filename


# 全局配置获取函数
_config: Optional[Config] = None

def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config
