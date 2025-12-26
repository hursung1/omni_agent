from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph, END
from langgraph_scripts.tools import *
from langgraph_scripts.graph_state import *

from typing import Any
from langchain_core.prompts import load_prompt
from langchain_core.messages import SystemMessage, HumanMessage


class DocumentRetriever:
    def __init__(self) -> None:
        self.graph = self.compile_graph()

    def compile_graph(self) -> CompiledStateGraph:
        graph = StateGraph(SearchAgentState)
        
        # add nodes
        graph.add_node("analyze_query", self.analyze_query)
        graph.add_node("retrieve", self.retrieve)
        graph.add_node("generate_answer", self.generate_answer)

        # add edges
        graph.set_entry_point("analyze_query")
        graph.add_edge("analyze_query", "retrieve")
        graph.add_edge("retrieve", "generate_answer")
        graph.add_edge("generate_answer", END)

        return graph.compile()
    
    async def run_graph(self, query: str, topk: int = 10, alpha: float = 0.75):
        state = {
            "query": query,
            "topk": topk,
            "alpha": alpha
        }
        return await self.graph.ainvoke(state)

    async def analyze_query(self, state: SearchAgentState) -> SearchAgentState:
        query = state["query"]
        system_prompt = load_prompt("prompts/rag_agent_clasify_intent.yaml", encoding="utf-8")
        user_prompt = f"""# User's query
{query}
"""

        intent = await base_llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        return {
            "intent": intent
        }

    async def retrieve(self, state: SearchAgentState) -> SearchAgentState:
        retriever = Worker(intent=state["intent"])
        retrieved_docs = await retriever(state["query"], state["topk"], state["alpha"])
        
        return {
            "retrieved_docs": retrieved_docs
        }
    
    async def generate_answer(self, state: SearchAgentState) -> SearchAgentState:
        user_query = state["query"]
        retrieved_docs = state["retrieved_docs"]

        formatted_docs = "\n\n".join([doc.page_content for doc in retrieved_docs])

        system_prompt = load_prompt("prompts/rag_agent_generate_answer.yaml", encoding="utf-8")
        user_prompt = f"""# User's query
{user_query}

# Documents
{formatted_docs}
"""

        prompt = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        from models.llm import base_llm
        generated_answer = await base_llm.ainvoke(prompt)

        return {
            "generated_answer": generated_answer
        }