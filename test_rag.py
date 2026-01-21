import sys
import os

# 将项目根目录添加到搜索路径
sys.path.append(os.getcwd())

from CV.rag_engine import get_rag_engine

def test_rag_capability():
    print("--- 🛠️ RAG 引擎底层能力测试 ---")
    
    # 1. 检查索引状态
    engine = get_rag_engine()
    if not engine.documents:
        print("❌ 错误：知识库未正确加载或为空！")
        return

    print(f"✅ 成功：已加载 {len(engine.documents)} 个文档块ảng。")

    # 2. 模拟典型教学提问
    test_queries = [
        "什么是新闻的真实性？",
        "如何描述实习经历中的突破性？",
        "新闻采访的基本要求是什么？"
    ]

    for q in test_queries:
        print(f"\n🙋 学生提问: {q}")
        response = engine.generate_response(q)
        print(response)

if __name__ == "__main__":
    test_rag_capability()