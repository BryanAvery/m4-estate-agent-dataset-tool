from __future__ import annotations

from dataclasses import asdict, replace

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from automation_layer.config import AutomationConfig
from automation_layer.service import AutomationLayerService

app = FastAPI(title="M4 Automation API")

# Allow GitHub Pages frontend and local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AutomationRunRequest(BaseModel):
    towns: list[str] = Field(default_factory=list)
    rightmoveUrls: list[str] = Field(default_factory=list)
    maxResults: int = Field(default=20, ge=1, le=100)
    googleMapsApiKey: str | None = None


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "API is running"}


@app.post("/api/automation/run")
def run_automation(payload: AutomationRunRequest) -> dict[str, list[dict]]:
    towns = [town.strip() for town in payload.towns if town and town.strip()]
    rightmove_urls = [url.strip() for url in payload.rightmoveUrls if url and url.strip()]

    if not towns and not rightmove_urls:
        raise HTTPException(status_code=400, detail="Provide at least one town or Rightmove URL.")

    try:
        config = AutomationConfig.from_env()
        if payload.googleMapsApiKey and payload.googleMapsApiKey.strip():
            config = replace(config, google_maps_api_key=payload.googleMapsApiKey.strip())
        service = AutomationLayerService(config)
        records = service.collect(
            towns=towns,
            rightmove_urls=rightmove_urls,
            max_results_each=payload.maxResults,
        )
    except Exception as error:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(error)) from error

    return {"records": [asdict(record) for record in records]}
