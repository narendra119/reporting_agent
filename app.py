from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    match = re.search(r"<json_reponse>\s*(.*?)\s*</json_reponse>", response, re.DOTALL)
    if not match:
        return None
    return json.loads(match.group(1))

@app.post("/api/report")
def get_report(body: ReportRequest):
    messages = run_agent(body.query, [])
    print(messages)
    last_assistant = next(
        m for m in reversed(messages) if m["role"] == "assistant"
    )
    text = " ".join(
        block.text for block in last_assistant["content"] if hasattr(block, "text")
    )
    return extract_json_from_response(text)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)