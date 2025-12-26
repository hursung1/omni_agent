import logging

from typing import Literal

from utils import get_chat_history
from models.llm import base_llm, tool_llm
from langgraph_scripts.tools import tools, TOOL_MAP
from langgraph_scripts.graph_state import AgentState

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import load_prompt
from langchain_core.output_parsers import PydanticOutputParser

logger = logging.getLogger(__name__)

async def orchestrator(state: AgentState) -> AgentState:
    """
    
    """
    msg_history = state["messages"]
    conv_history = get_chat_history(msg_history)

    system_prompt = load_prompt("prompts/orchestrator.yaml", encoding="utf-8").template
    # logger.info(f"[orchestrator] System prompt\n---\n{system_prompt.template}")
    return_state = {}
    try:
        ai_msg = await tool_llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=conv_history)
        ])
        
        return_state["messages"] = [ai_msg]

    except Exception as e:
        logger.error(f"[orchestrator] Exception: {str(e)}")

    return return_state


async def should_continue(state: AgentState) -> Literal["tool", "next"]:
    last_msg = state["messages"][-1]
    tool_name = getattr(last_msg, "tool_calls", None)

    if (isinstance(last_msg, AIMessage) and tool_name == "generate_answer") or state["num_tries"] > 2:
        return "next"
    else:
        return "tool"
    

async def execute_tools(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1]

    retrieved_results = {
        "messages": [],
        "num_tries": state["num_tries"] + 1
    }

    for call in getattr(last_msg, "tool_calls", []):
        tool_name = call.get("name")
        args = call.get("args")
        tool_call_id = call.get("id")

        if not (tool_name and tool_call_id and (tool_name in TOOL_MAP.keys())):
            continue
        
        tool = TOOL_MAP[tool_name]
        try:
            result = await tool.ainvoke(args)
            if type(result) is list:
                tool_msg_content = "\n\n".join([doc.page_content for doc in result])

            elif type(result) is str:
                tool_msg_content = result

            else:
                tool_msg_content = ""

        except Exception as e:
            logger.error(f"[execute_tools] Exception: {str(e)}")


        retrieved_results["messages"].append(
            ToolMessage(content=tool_msg_content, tool_call_id=tool_call_id)
        )
        retrieved_results[f"{tool_name}_results"] = result

    return retrieved_results


async def generate_answer(state: AgentState) -> AgentState:
    chat_history = get_chat_history(state["messages"])
    answer = ""
    system_prompt = load_prompt("prompts/generate_answer.yaml", encoding="utf-8").template

    chunk_stream = base_llm.astream([
        SystemMessage(content=system_prompt),
        HumanMessage(content=chat_history)
    ])

    async for chunk in chunk_stream:
        answer += chunk.content

    return {
        "messages": [AIMessage(content=answer)]
    }