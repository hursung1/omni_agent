from langgraph_scripts.tools import *
from langgraph_scripts.graph_state import *
from models.llm import base_llm

from typing import Any
from langchain_core.prompts import load_prompt
from langchain_core.messages import SystemMessage, HumanMessage


class DocumentRetriever:
    def __init__(self) -> None:
        pass

    async def analyze_query(self, state: str) -> :
        prompt = load_prompt("", encoding="utf-8")
        
        structured_llm = base_llm.with_structured_output(Intent)
        user_intent = await structured_llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=query)
        ])




    async def retrieve(self, ) -> Any:
        pass 