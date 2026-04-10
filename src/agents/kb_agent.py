
from typing import List, Dict, Any
import litellm

from src.agents.state import AgentState
from src.config.settings import settings
from src.rag.retriever import retrieve_documents


class KnowledgeBaseAgent:
    """知识库Agent：RAG检索、文档问答"""

    def __init__(self):
        self.model = settings.litellm_model

    def retrieve_information(self, query: str) -> List[str]:
        """从向量库检索相关信息"""
        try:
            docs = retrieve_documents(query)
            return [doc.page_content for doc in docs[:3]]  # 返回前3个最相关文档
        except Exception as e:
            return [f"检索失败: {str(e)}"]

    def generate_answer(self, query: str, context: List[str]) -> str:
        """基于检索到的上下文生成答案"""
        if not context or "检索失败" in context[0]:
            return "无法从知识库中找到相关信息。"

        context_text = "\n\n".join(context)
        prompt = f"""
        基于以下上下文信息，回答用户问题。
        
        上下文信息：
        {context_text}
        
        用户问题：{query}
        
        请给出准确、完整的回答，如果信息不足请说明。
        """

        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个基于知识库回答问题的助手"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    def process(self, state: AgentState) -> AgentState:
        """处理知识库查询"""
        user_input = state["user_input"]

        # 检索相关信息
        retrieved_docs = self.retrieve_information(user_input)

        # 生成答案
        answer = self.generate_answer(user_input, retrieved_docs)

        # 更新状态
        state["retrieved_docs"] = retrieved_docs
        state["tool_results"]["kb_answer"] = answer

        # 添加消息
        state["messages"].append({
            "role": "assistant",
            "content": f"知识库检索完成，找到 {len(retrieved_docs)} 条相关信息"
        })

        return state


def kb_node(state: AgentState) -> AgentState:
    """知识库节点函数，用于LangGraph"""
    agent = KnowledgeBaseAgent()
    return agent.process(state)