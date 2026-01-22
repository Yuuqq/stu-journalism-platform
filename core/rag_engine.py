"""
RAG (Retrieval-Augmented Generation) 引擎
基于 TF-IDF 的本地知识库检索系统

该模块提供：
- SearchResult: 检索结果数据结构
- RAGEngine: 本地 RAG 引擎，支持 PDF、TXT、MD 文件
- get_rag_engine: 获取全局 RAG 引擎实例

Features:
- 使用字符级 N-gram 适配中文
- 滑动窗口分块提高匹配精度
- 支持增量索引
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Set, FrozenSet

import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass, field

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .config import get_config

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """检索结果

    Attributes:
        source: 来源文件名
        content: 匹配的文本内容
        score: 相似度分数 (0-1)
    """
    source: str
    content: str
    score: float

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "source": self.source,
            "content": self.content,
            "score": round(self.score, 4)
        }


class RAGEngine:
    """
    本地 RAG 引擎

    特性:
    - 支持 PDF、TXT、MD 文件
    - 使用字符级 N-gram 适配中文
    - 滑动窗口分块提高匹配精度
    - 延迟索引，按需加载
    """

    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS: Set[str] = {'.pdf', '.txt', '.md'}

    def __init__(self, corpus_path: Optional[Path] = None):
        """初始化 RAG 引擎

        Args:
            corpus_path: 语料库路径，默认使用配置中的路径
        """
        self.config = get_config()
        self.corpus_path = corpus_path or self.config.paths.corpus

        self.documents: List[str] = []
        self.filenames: List[str] = []
        self.chunk_metadata: List[Dict] = []
        self._indexed_files: Set[str] = set()  # 已索引的文件

        # 使用字符级 N-gram 匹配，完美适配中文
        rag_config = self.config.rag
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=rag_config.ngram_range
        )
        self.tfidf_matrix = None

        self._index_corpus()

    def _index_corpus(self) -> None:
        """索引语料库"""
        if not self.corpus_path.exists():
            logger.warning(f"Corpus path does not exist: {self.corpus_path}")
            return

        file_count = 0
        for file_path in self.corpus_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                if str(file_path) not in self._indexed_files:
                    self._process_file(file_path)
                    self._indexed_files.add(str(file_path))
                    file_count += 1

        if self.documents:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
            logger.info(f"RAG Engine indexed {len(self.documents)} chunks from {len(self._indexed_files)} files")

    def _process_file(self, file_path: Path) -> None:
        """处理单个文件

        Args:
            file_path: 文件路径
        """
        try:
            text = self._extract_text(file_path)
            if text:
                self._chunk_text(text, file_path.name)
                logger.debug(f"Processed: {file_path.name}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

    def _extract_text(self, file_path: Path) -> str:
        """从文件提取文本"""
        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            return self._extract_pdf(file_path)
        elif suffix in ('.txt', '.md'):
            return self._extract_text_file(file_path)

        return ""

    def _extract_pdf(self, file_path: Path) -> str:
        """提取 PDF 文本"""
        if PyPDF2 is None:
            logger.warning("PyPDF2 not installed, skipping PDF file")
            return ""

        text_parts: List[str] = []
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return ""
        return "\n".join(text_parts)

    def _extract_text_file(self, file_path: Path) -> str:
        """提取文本文件内容"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def _chunk_text(self, text: str, filename: str) -> None:
        """将文本分块"""
        rag_config = self.config.rag
        chunk_size = rag_config.chunk_size
        overlap = rag_config.chunk_overlap
        min_length = rag_config.min_chunk_length

        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if len(chunk) > min_length:
                self.documents.append(chunk)
                self.filenames.append(filename)
                self.chunk_metadata.append({
                    "start": i,
                    "end": i + len(chunk),
                    "filename": filename
                })

    def query(self, user_query: str, top_k: Optional[int] = None) -> List[SearchResult]:
        """
        检索相关文档

        Args:
            user_query: 用户查询
            top_k: 返回结果数量

        Returns:
            检索结果列表，按相关度降序
        """
        if self.tfidf_matrix is None or not self.documents:
            return []

        top_k = top_k or self.config.rag.top_k

        # 清洗查询（移除常见停用词）
        cleaned_query = self._clean_query(user_query)

        # 向量化并计算相似度
        query_vec = self.vectorizer.transform([cleaned_query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # 获取 top-k 结果
        top_indices = similarities.argsort()[:-top_k-1:-1]

        results = []
        threshold = self.config.rag.similarity_threshold

        for idx in top_indices:
            if similarities[idx] > threshold:
                results.append(SearchResult(
                    source=self.filenames[idx],
                    content=self.documents[idx].strip(),
                    score=float(similarities[idx])
                ))

        return results

    def _clean_query(self, query: str) -> str:
        """清洗用户查询"""
        # 移除常见中文停用词和标点
        stopwords = r'[什么是的？?吗如何怎么为什么\s]'
        cleaned = re.sub(stopwords, '', query)
        return cleaned if cleaned else query

    def generate_response(self, user_query: str) -> str:
        """
        生成 AI 回复

        Args:
            user_query: 用户问题

        Returns:
            格式化的 AI 回复
        """
        results = self.query(user_query)

        if not results:
            return self._generate_not_found_response(user_query)

        return self._format_response(user_query, results)

    def _generate_not_found_response(self, query: str) -> str:
        """生成未找到结果的回复"""
        return (
            f"🤖 **AI 分析**：\n\n"
            f"在现有课程资料中暂未找到关于「{query}」的具体描述。\n\n"
            f"**建议**：\n"
            f"- 尝试使用更具体的关键词\n"
            f"- 检查 assets/corpus 目录下是否已添加相关文档"
        )

    def _format_response(self, query: str, results: List[SearchResult]) -> str:
        """格式化检索结果为回复"""
        response = f"🤖 **基于校内课程资料的 AI 回复**：\n\n"
        response += f"关于「**{query}**」，我在资料库中找到了相关内容：\n\n"

        for i, res in enumerate(results, 1):
            clean_content = res.content.replace('\n', ' ')
            response += f"> **📑 来源：{res.source}** (匹配度: {res.score:.2f})\n"
            response += f"> *\"...{clean_content}...\"*\n\n"

        return response

    def get_stats(self) -> Dict:
        """获取引擎统计信息"""
        return {
            "total_chunks": len(self.documents),
            "total_files": len(set(self.filenames)),
            "files": list(set(self.filenames)),
            "indexed": self.tfidf_matrix is not None
        }


# 全局 RAG 引擎实例
_rag_instance: Optional[RAGEngine] = None

def get_rag_engine() -> RAGEngine:
    """获取全局 RAG 引擎实例"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGEngine()
    return _rag_instance
