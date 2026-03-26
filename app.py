import asyncio
import json
import queue
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from agent.loop import run_agent

app = FastAPI()

# IMPORTANT: This allows your React app (on port 5173) to talk to Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReportRequest(BaseModel):
    query: str

def extract_json_from_response(response: str):
    import re, json
    match = re.search(r"<json_response>\s*(.*?)\s*</json_response>", response, re.DOTALL)
    if not match:
        return None
    return json.loads(match.group(1))

def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.post("/api/report/stream")
async def stream_report(body: ReportRequest):
    q: queue.Queue = queue.Queue()
    DONE = object()

    def on_event(payload: dict) -> None:
        q.put(dict(payload))

    def worker():
        try:
            messages = run_agent(body.query, [], on_event)
            q.put({"_messages": messages})
        except Exception as e:
            q.put({"_error": str(e)})
        finally:
            q.put(DONE)

    threading.Thread(target=worker, daemon=True).start()

    async def generate():
        loop = asyncio.get_event_loop()
        while True:
            item = await loop.run_in_executor(None, q.get)
            if item is DONE:
                break
            if "_error" in item:
                yield _sse("error", {"message": item["_error"]})
                return
            if "_messages" in item:
                last = next((m for m in reversed(item["_messages"]) if m["role"] == "assistant"), None)
                if last:
                    text = " ".join(b.text for b in last["content"] if hasattr(b, "text") and b.text)
                    parsed = extract_json_from_response(text)
                    if parsed:
                        yield _sse("done", parsed)
                continue
            event_type = item.pop("type")
            yield _sse(event_type, item)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/report")
def get_report(body: ReportRequest):
    messages = run_agent(body.query, [])
    last_assistant = next(
        m for m in reversed(messages) if m["role"] == "assistant"
    )
    text = " ".join(
        block.text for block in last_assistant["content"] if block.text is not None
    )
    return extract_json_from_response(text)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)