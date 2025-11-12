import os
import requests

from typing import List
from langchain_core.messages import (
    AnyMessage, 
    SystemMessage, 
    HumanMessage, 
    AIMessage, 
    ToolMessage
)


def get_chat_history(messages: List[AnyMessage]):
    chat_history = ""
    for msg in messages:
        if isinstance(msg, SystemMessage):
            chat_history += f"- System: {msg.content}\n"
        elif isinstance(msg, HumanMessage):
            chat_history += f"- User: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            chat_history += f"- Assistant: {msg.content}\n"
        elif isinstance(msg, ToolMessage):
            chat_history += f"- Tool use: {msg.content}\n"

    return chat_history


def safe_filename(filename):
    """
    파일명이 안전한지 확인하고, 필요하면 파일명을 안전하게 수정
    """
    filename = filename.encode("utf-8", "ignore").decode("utf-8")
    filename = os.path.basename(filename)
    filename = filename.replace(" ", "_")

    return filename

def call_llm(prompt: str = "", user_input: str = "") -> dict:
    """
    Genos LLM 호출하는 함수
    """
    token = "b37080c0a4f747d9978f8bd1c4f6ecce"
    url = "https://genos.genon.ai:3443/api/gateway/rep/serving/43"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "model": "google/gemini-2.5-pro-preview",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ]
    }
    response = requests.post(url=f"{url}/v1/chat/completions", headers=headers, json=data)
    return response.json()["choices"][0]["message"]