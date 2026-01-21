"""
统一配置管理模块
集中管理所有路径、常量和系统设置
"""
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional

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
    """RAG 引擎配置"""
    chunk_size: int = 200
    chunk_overlap: int = 40
    min_chunk_length: int = 10
    ngram_range: tuple = (2, 4)
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
        """安全加载 JSON 文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Config file not found: {path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {path}: {e}")
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
