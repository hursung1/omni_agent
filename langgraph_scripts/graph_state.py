from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from langgraph.graph import MessagesState

from typing import List
from pydantic import BaseModel, Field


class AgentState(MessagesState):
    user_input: str
    hr_doc_retriever_results: List[Document]
    wiki_doc_retriever_results: List[Document]
    translator_results: str
    num_tries: int


class FinalAnswer(BaseModel):
    reasoning: str
    answer: str


class DocRetrieverArgs(BaseModel):
    query: str = Field(
        ...,
        description="Query or keywords for serach. Must be KOREAN."
    )
    topk: int = Field(
        ...,
        description="The number of documents to retrieve."
    )
    alpha: float = Field(
        ...,
        description="Parameter for weighted sum between keyword search and vector search."
    )