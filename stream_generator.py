import json
import time
import logging

from langchain_core.messages import AIMessageChunk

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langgraph_scripts.graph_nodes import *
from langgraph_scripts.graph_state import AgentState

logger = logging.getLogger(__name__)

class StreamingService:
    def __init__(self):
        self.graph = self.compile_graph()

    def compile_graph(self) -> CompiledStateGraph:
        graph = StateGraph(AgentState)

        # Define nodes
        graph.add_node("orchestrator", orchestrator)
        graph.add_node("execute_tools", execute_tools)
        graph.add_node("generate_answer", generate_answer)

        # define edge
        graph.set_entry_point("orchestrator")
        graph.add_conditional_edges("orchestrator", should_continue, {
            "tool": "execute_tools",
            "next": "generate_answer"
        })
        graph.add_edge("execute_tools", "orchestrator")
        agent_graph = graph.compile()

        return agent_graph
    
    async def stream_service(self, query: str):
        input_state = {
            "user_input": query,
            "messages": [HumanMessage(content=query)],
            "num_tries": 0
        }

        is_first_token = True
        start_time = time.time()
        return_data = {"status": "done"}

        try:
            async for chunk, meta in self.graph.astream(input_state, stream_mode="messages"):
                node = meta.get("langgraph_node", "")
                if node != "generate_answer": continue

                if is_first_token:
                    is_first_token = not is_first_token
                    first_token_time = time.time()

                yield self._format_sse("stream", {"data": chunk.content})

            end_time = time.time()
            return_data["ttft"] = first_token_time - start_time
            return_data["e2el"] = end_time - start_time

        except Exception as e:
            ...
            yield self._format_sse("error", {"data": str(e)})

        finally:
            yield self._format_sse("finished", return_data)



    def _format_sse(self, type: str, data: dict) -> str:
        return f"event: {type}\ndata: {json.dumps(data)}\n\n"