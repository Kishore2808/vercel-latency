from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from pydantic import BaseModel
from pathlib import Path
import json
import numpy as np

app = FastAPI()

# Always attach permissive CORS headers (some validators expect them even without Origin).
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("Access-Control-Allow-Origin", "*")
    response.headers.setdefault("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.setdefault("Access-Control-Allow-Headers", "*")
    return response

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data
TELEMETRY_PATH = Path(__file__).resolve().parent / "_telemetry.json"
with TELEMETRY_PATH.open() as f:
    telemetry = json.load(f)

class RequestData(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.options("/{full_path:path}")
def preflight_handler(full_path: str):
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

@app.post("/")
def analyze(data: RequestData):
    result = {}

    for region in data.regions:
        records = [r for r in telemetry if r["region"] == region]

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        if not records:
            continue

        result[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": sum(1 for l in latencies if l > data.threshold_ms)
        }

    return result
