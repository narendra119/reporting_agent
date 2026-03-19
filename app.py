from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# IMPORTANT: This allows your React app (on port 5173) to talk to Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/report")
async def get_report():
    # This dummy data matches the keys in your React code
    return [
        {"name": "Jan", "revenue": 4500, "orders": 2400},
        {"name": "Feb", "revenue": 3200, "orders": 1398},
        {"name": "Mar", "revenue": 4800, "orders": 9800},
        {"name": "Apr", "revenue": 5100, "orders": 3908},
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)