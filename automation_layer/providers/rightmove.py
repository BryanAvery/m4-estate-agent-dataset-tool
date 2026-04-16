from __future__ import annotations

import json
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

from automation_layer.config import AutomationConfig
from automation_layer.models import LeadRecord


class RightmoveProvider:
    """Collects estate agency names from Rightmove search result pages.

    This parser is intentionally defensive because Rightmove's page structure
    changes periodically.
    """

    def __init__(self, config: AutomationConfig) -> None:
        self._config = config

    def pull_from_search_page(self, search_url: str, max_results: int = 40) -> list[LeadRecord]:
        headers = {"User-Agent": self._config.user_agent}
        response = requests.get(
            search_url,
            headers=headers,
            timeout=self._config.request_timeout_seconds,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.find("script", id="__NEXT_DATA__")
        captured_on = date.today().isoformat()

        if not script_tag or not script_tag.text.strip():
            return self._fallback_parse_from_html(soup, search_url, captured_on, max_results)

        data = json.loads(script_tag.text)
        listings = self._extract_listings(data)

        records: list[LeadRecord] = []
        for listing in listings[:max_results]:
            branch_name = (
                listing.get("customer", {}).get("branchDisplayName")
                or listing.get("customer", {}).get("brandTradingName")
                or "Unknown"
            )
            location = listing.get("displayAddress") or listing.get("location", {}).get("name", "")
            listing_id = listing.get("id")

            records.append(
                LeadRecord(
                    business_name=branch_name,
                    location=location,
                    notes=f"Rightmove listing id: {listing_id}",
                    source_url=(
                        f"https://www.rightmove.co.uk/properties/{listing_id}"
                        if listing_id
                        else search_url
                    ),
                    date_captured=captured_on,
                )
            )

        return records

    def _extract_listings(self, payload: dict) -> list[dict]:
        stack = [payload]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                if "properties" in current and isinstance(current["properties"], list):
                    return current["properties"]
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)
        return []

    def _fallback_parse_from_html(
        self,
        soup: BeautifulSoup,
        source_url: str,
        captured_on: str,
        max_results: int,
    ) -> list[LeadRecord]:
        text = soup.get_text(" ", strip=True)
        agencies = set(re.findall(r"[A-Z][A-Za-z0-9&'\- ]+ (?:Estate Agents|Lettings|Properties)", text))
        records = [
            LeadRecord(
                business_name=name,
                location="",
                notes="Parsed from Rightmove HTML fallback",
                source_url=source_url,
                date_captured=captured_on,
            )
            for name in sorted(agencies)
        ]
        return records[:max_results]
