import logging
import uvicorn

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from pydantic import BaseModel
from stream_generator import StreamingService

from langchain.globals import set_debug

app = FastAPI()
service_name = "Omni-Agent"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

set_debug(True)
logging.getLogger("langchain").setLevel(logging.DEBUG)
logging.getLogger("elasticsearch").setLevel(logging.DEBUG)
logging.getLogger("langchain_community.vectorstores.elasticsearch").setLevel(logging.DEBUG)

service = StreamingService()

class SearchRequest(BaseModel):
    query: str

# main window
@app.get("/")
async def root():
    return {"message": "hi"}


@app.post("/search/")
async def search(request: SearchRequest):
    """
    사용자가 보낸 메시지를 LLM에 전송하고, 그 응답을 대화 이력에 추가하고, 응답을 return
    """
    global service
    generator = service.stream_service(request.query)

    response_headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*"
    }
    return StreamingResponse(
        generator, 
        media_type="text/event-stream",
        headers=response_headers    
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)