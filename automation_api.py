from __future__ import annotations

import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from automation_layer.config import AutomationConfig
from automation_layer.service import AutomationLayerService


class AutomationApiHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send_json(200, {"ok": True})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/automation/run":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            request_body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(request_body or "{}")

            towns = [str(x).strip() for x in payload.get("towns", []) if str(x).strip()]
            rightmove_urls = [str(x).strip() for x in payload.get("rightmoveUrls", []) if str(x).strip()]
            max_results = int(payload.get("maxResults", 20))

            if not towns and not rightmove_urls:
                self._send_json(400, {"error": "Provide at least one town or Rightmove URL."})
                return

            config = AutomationConfig.from_env()
            service = AutomationLayerService(config)
            records = service.collect(
                towns=towns,
                rightmove_urls=rightmove_urls,
                max_results_each=max_results,
            )
            self._send_json(200, {"records": [asdict(record) for record in records]})
        except Exception as error:  # noqa: BLE001
            self._send_json(500, {"error": str(error)})


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 8787), AutomationApiHandler)
    print("Automation API listening on http://localhost:8787")
    server.serve_forever()


if __name__ == "__main__":
    main()
