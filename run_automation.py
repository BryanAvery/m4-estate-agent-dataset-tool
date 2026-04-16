from __future__ import annotations

import argparse

from automation_layer.config import AutomationConfig
from automation_layer.service import AutomationLayerService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pull estate agent leads from Google Maps and Rightmove into CSV.",
    )
    parser.add_argument(
        "--town",
        action="append",
        default=[],
        help="Town to search on Google Maps. Repeat for multiple towns.",
    )
    parser.add_argument(
        "--rightmove-url",
        action="append",
        default=[],
        help="Rightmove search result URL. Repeat for multiple pages.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=20,
        help="Maximum records to pull from each town/url.",
    )
    parser.add_argument(
        "--output",
        default="outputs/estate_agents.csv",
        help="Output CSV path.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.town and not args.rightmove_url:
        parser.error("Provide at least one --town or --rightmove-url value.")

    config = AutomationConfig.from_env()
    service = AutomationLayerService(config)
    records = service.collect(
        towns=args.town,
        rightmove_urls=args.rightmove_url,
        max_results_each=args.max_results,
    )
    service.write_csv(records, args.output)
    print(f"Wrote {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
