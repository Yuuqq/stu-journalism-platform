import os
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

class LocalRAG:
    def __init__(self, corpus_path):
        self.corpus_path = corpus_path
        self.documents = []  
        self.filenames = []  
        # 终极修改：使用字符级 N-gram 匹配 (2到4个字符)，完美适配中文
        self.vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
        self.tfidf_matrix = None
        self._load_and_index()

    def _load_and_index(self):
        if not os.path.exists(self.corpus_path):
            return

        for root, dirs, files in os.walk(self.corpus_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    text = ""
                    if file.lower().endswith('.pdf'):
                        with open(file_path, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            for page in reader.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    text += page_text + "\n"
                    elif file.lower().endswith(('.txt', '.md')):
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                    
                    if text:
                        # 再次缩小块大小，提高匹配精度
                        chunk_size = 200
                        overlap = 40
                        for i in range(0, len(text), chunk_size - overlap):
                            chunk = text[i:i + chunk_size]
                            if len(chunk) > 10: 
                                self.documents.append(chunk)
                                self.filenames.append(file)
                                
                except Exception as e:
                    print(f"Error reading {file}: {e}")

        if self.documents:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)

    def query(self, user_query, top_k=2):
        if self.tfidf_matrix is None or not self.documents:
            return []

        # 简单清洗提问
        q = re.sub(r'[什么是的？?吗如何\s]', '', user_query)
        if not q: q = user_query

        query_vec = self.vectorizer.transform([q])
        cosine_similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        related_docs_indices = cosine_similarities.argsort()[:-top_k-1:-1]
        
        results = []
        for idx in related_docs_indices:
            # 只要有一定相关度就返回
            if cosine_similarities[idx] > 0.02: 
                results.append({
                    "source": self.filenames[idx],
                    "content": self.documents[idx].strip(),
                    "score": cosine_similarities[idx]
                })
        
        return results

    def generate_response(self, user_query):
        results = self.query(user_query)
        
        if not results:
            return f"🤖 **AI 分析**：在现有课程资料中暂未找到关于“{user_query}”的具体描述。建议检查 CV/assets/corpus 目录下的文档内容。"

        response = f"🤖 **基于校内课程资料的 AI 回复**：\n\n"
        response += f"关于“**{user_query}**”，我在资料库中找到了相关线索：\n\n"
        
        for i, res in enumerate(results, 1):
            clean_content = res['content'].replace('\n', ' ')
            response += f"> **📑 来源：{res['source']}** (匹配度: {res['score']:.2f})\n"
            response += f"> *“...{clean_content}...”*\n\n"
            
        return response

_rag_instance = None
def get_rag_engine():
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = LocalRAG('CV/assets/corpus')
    return _rag_instance
