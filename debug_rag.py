import sys
import os
sys.path.append(os.getcwd())
from CV.rag_engine import get_rag_engine

def debug_rag_content():
    engine = get_rag_engine()
    print(f"--- 🔍 知识库内容诊断 (前5块) ---")
    for i, chunk in enumerate(engine.documents[:5]):
        print(f"Chunk {i}: {chunk[:100]}...")
        
    print("\n--- 🧠 词频分析 (关键词) ---")
    if hasattr(engine.vectorizer, 'get_feature_names_out'):
        features = engine.vectorizer.get_feature_names_out()
        print(f"Top 20 features: {list(features)[:20]}")

if __name__ == "__main__":
    debug_rag_content()

