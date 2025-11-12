from typing import Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser

class Worker:
    def __init__(self, intent: str) -> None:
        self.intent = intent

    async def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass
