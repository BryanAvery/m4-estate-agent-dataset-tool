from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path

from automation_layer.config import AutomationConfig
from automation_layer.models import LeadRecord
from automation_layer.providers.google_maps import GoogleMapsProvider
from automation_layer.providers.rightmove import RightmoveProvider


class AutomationLayerService:
    def __init__(self, config: AutomationConfig) -> None:
        self.google_maps = GoogleMapsProvider(config)
        self.rightmove = RightmoveProvider(config)

    def collect(self, towns: list[str], rightmove_urls: list[str], max_results_each: int = 20) -> list[LeadRecord]:
        all_records: list[LeadRecord] = []

        for town in towns:
            all_records.extend(self.google_maps.search_estate_agents(town=town, max_results=max_results_each))

        for url in rightmove_urls:
            all_records.extend(self.rightmove.pull_from_search_page(search_url=url, max_results=max_results_each))

        return self._dedupe(all_records)

    def write_csv(self, records: list[LeadRecord], output_path: str | Path) -> None:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", newline="", encoding="utf-8") as f:
            if not records:
                return
            writer = csv.DictWriter(f, fieldnames=list(asdict(records[0]).keys()))
            writer.writeheader()
            for row in records:
                writer.writerow(asdict(row))

    def _dedupe(self, records: list[LeadRecord]) -> list[LeadRecord]:
        seen: set[tuple[str, str]] = set()
        unique: list[LeadRecord] = []
        for record in records:
            key = (record.business_name.strip().lower(), record.location.strip().lower())
            if key in seen:
                continue
            seen.add(key)
            unique.append(record)
        return unique
