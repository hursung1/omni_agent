from typing import List

from retriever.workers import Worker

from langgraph_scripts.graph_state import DocRetrieverArgs
# from retriever.reranker import rrkr

from langchain.tools import tool

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatMessagePromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser

@tool(args_schema=DocRetrieverArgs)
async def hr_doc_retriever(query: str, topk: int = 10, alpha: float = 0.75):
    """
    사내 인사/복지 제도에 관한 질의를 가지고 사내 HR 문서를 검색
    """

    # retriever = HRSearchWorker("HR")
    retriever = Worker(intent="HR")
    retrieved_docs = await retriever(query, topk, alpha)
    return retrieved_docs
    reranked_docs = await rrkr.rerank(query, retrieved_docs)

    return reranked_docs


@tool(args_schema=DocRetrieverArgs)
async def wiki_doc_retriever(query: str, topk: int = 10, alpha: float = 0.75):
    """
    일반 상식에 관한 질의를 가지고 Wikipedia 문서를 검색
    """
    retriever = Worker(intent="wiki")
    retrieved_docs = await retriever(query, topk, alpha)
    return retrieved_docs
    

@tool
async def generate_answer():
    """
    답변 제공에 충분한 배경 지식과 검색 결과를 가지고 있는 경우, 혹은 어떤 tool을 선택해도 적절한 정보를 제공하지 못하는 경우로 판단될 때만 호출해야 한다.
    """
    return

tools = [
    hr_doc_retriever,
    wiki_doc_retriever,
    generate_answer
]

TOOL_MAP = {
    "hr_doc_retriever": hr_doc_retriever,
    "wiki_doc_retriever": wiki_doc_retriever,
    "generate_answer": generate_answer
}