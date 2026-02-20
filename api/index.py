from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json
import numpy as np

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry data
TELEMETRY_PATH = Path(__file__).resolve().parent / "_telemetry.json"
with TELEMETRY_PATH.open() as f:
    telemetry = json.load(f)

class RequestData(BaseModel):
    regions: list[str]
    threshold_ms: float

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
