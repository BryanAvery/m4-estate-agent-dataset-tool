from __future__ import annotations

import json
import os
from dataclasses import asdict, replace

import requests
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


class AiEnrichmentRecord(BaseModel):
    id: str
    business_name: str | None = None
    branch_name: str | None = None
    location: str | None = None
    postcode: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    service_type: str | None = None
    source_url: str | None = None
    notes: str | None = None


class AiEnrichmentRequest(BaseModel):
    record: AiEnrichmentRecord
    model: str = "gpt-5.4-mini"
    openAiApiKey: str | None = None
    prompt: str | None = None


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


@app.post("/api/ai/enrich-record")
def enrich_record(payload: AiEnrichmentRequest) -> dict:
    api_key = (payload.openAiApiKey or os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured.")

    model = payload.model.strip() or "gpt-5.4-mini"
    input_record = payload.record.model_dump()

    prompt = (payload.prompt or "").strip()
    if not prompt:
        prompt = (
            "You are enriching an estate agent dataset record for lead generation.\n\n"
            "Rules:\n"
            "- Do not invent facts\n"
            "- Do not guess exact contact details\n"
            "- Use null where uncertain\n"
            "- Return JSON only\n"
            "- Keep all values concise and database-friendly\n"
            "- Mark output as AI-generated\n\n"
            "Input:\n"
            f"{json.dumps(input_record, ensure_ascii=False)}\n\n"
            "Output JSON:\n"
            "{\n"
            f"  \"record_id\": \"{input_record['id']}\",\n"
            "  \"business_name_cleaned\": null,\n"
            "  \"business_type\": null,\n"
            "  \"services_offered\": [],\n"
            "  \"business_summary\": null,\n"
            "  \"outreach_relevance\": null,\n"
            "  \"outreach_reason\": null,\n"
            "  \"manual_research_needed\": [],\n"
            "  \"ai_confidence\": null,\n"
            "  \"ai_generated\": true\n"
            "}"
        )

    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            timeout=60,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "input": prompt,
                "temperature": 0.2,
                "text": {"format": {"type": "json_object"}},
            },
        )
    except requests.RequestException as error:
        raise HTTPException(status_code=502, detail=f"OpenAI request failed: {error}") from error

    if not response.ok:
        detail = response.text[:500]
        raise HTTPException(status_code=response.status_code, detail=f"OpenAI API error: {detail}")

    payload_json = response.json()
    output_text = payload_json.get("output_text") or ""
    if not output_text:
        chunks: list[str] = []
        for segment in payload_json.get("output", []):
            for part in segment.get("content", []):
                text = part.get("text")
                if text:
                    chunks.append(text)
        output_text = "\n".join(chunks).strip()

    if not output_text:
        raise HTTPException(status_code=500, detail="OpenAI response did not include text output.")

    try:
        result = json.loads(output_text)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=500, detail=f"Model returned invalid JSON: {error}") from error

    return {"record_id": input_record["id"], "ai_research": result, "ai_generated": True}
