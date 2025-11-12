import os
from uuid import uuid1

from langchain_openai import ChatOpenAI
from langgraph_scripts.tools import *

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
MODEL_NAME="gemini-2.5-flash"
API_KEY = os.environ["GEMINI_API_KEY"]

base_llm = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
    temperature=0,
    max_completion_tokens=8000,
    verbose=True,
    streaming=True
)

tool_llm = base_llm.bind_tools(tools=tools, tool_choice="required", strict=True)