from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AutomationConfig:
    """Runtime configuration for data collection providers."""

    google_maps_api_key: str | None
    user_agent: str
    request_timeout_seconds: int = 20

    @classmethod
    def from_env(cls) -> "AutomationConfig":
        return cls(
            google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY"),
            user_agent=os.getenv(
                "AUTOMATION_USER_AGENT",
                "m4-estate-agent-automation/1.0 (+https://example.local)",
            ),
            request_timeout_seconds=int(os.getenv("AUTOMATION_TIMEOUT_SECONDS", "20")),
        )
