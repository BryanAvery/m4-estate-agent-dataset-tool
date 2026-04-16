from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LeadRecord:
    business_name: str
    location: str
    postcode: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    services: str = "Sales,Lettings"
    notes: str = ""
    source_url: str = ""
    date_captured: str = ""
    status: str = "New"
