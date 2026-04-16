from __future__ import annotations

from datetime import date
from typing import Any

import requests

from automation_layer.config import AutomationConfig
from automation_layer.models import LeadRecord

_GOOGLE_TEXT_SEARCH_ENDPOINT = "https://maps.googleapis.com/maps/api/place/textsearch/json"


class GoogleMapsProvider:
    def __init__(self, config: AutomationConfig) -> None:
        self._config = config

    def search_estate_agents(self, town: str, max_results: int = 20) -> list[LeadRecord]:
        if not self._config.google_maps_api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY is required to pull Google Maps results.")

        params = {
            "query": f"estate agents in {town}",
            "key": self._config.google_maps_api_key,
        }
        headers = {"User-Agent": self._config.user_agent}

        response = requests.get(
            _GOOGLE_TEXT_SEARCH_ENDPOINT,
            params=params,
            headers=headers,
            timeout=self._config.request_timeout_seconds,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()

        items = payload.get("results", [])[:max_results]
        captured_on = date.today().isoformat()
        records: list[LeadRecord] = []

        for item in items:
            records.append(
                LeadRecord(
                    business_name=item.get("name", "Unknown"),
                    location=item.get("formatted_address", town),
                    notes=f"Google rating: {item.get('rating', 'N/A')} ({item.get('user_ratings_total', 0)} reviews)",
                    source_url=(
                        f"https://www.google.com/maps/place/?q=place_id:{item.get('place_id')}"
                        if item.get("place_id")
                        else ""
                    ),
                    date_captured=captured_on,
                )
            )

        return records
