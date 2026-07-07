"""Enterprise-layer tests: config, metrics, hardened HTTP service."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from almeezan.config import load_config
from almeezan.observability import Metrics
from almeezan.version import __version__
from almeezan.web import Handler, create_server


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = {k: os.environ.get(k) for k in (
            "ALMEEZAN_HOME", "ALMEEZAN_LEDGER", "ALMEEZAN_API_KEY",
            "ALMEEZAN_PORT", "ALMEEZAN_MAX_BODY_BYTES", "ALMEEZAN_LOG_LEVEL",
        )}

    def tearDown(self) -> None:
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_defaults(self) -> None:
        for key in self._saved:
            os.environ.pop(key, None)
        cfg = load_config()
        self.assertEqual(cfg.port, 8787)
        self.assertFalse(cfg.auth_required)
        self.assertTrue(str(cfg.ledger_path).endswith("almeezan-ledger.jsonl"))

    def test_env_overrides(self) -> None:
        os.environ["ALMEEZAN_HOME"] = str(Path(tempfile.gettempdir()) / "almeezan-home")
        os.environ["ALMEEZAN_API_KEY"] = "k-123"
        os.environ["ALMEEZAN_PORT"] = "9911"
        os.environ["ALMEEZAN_MAX_BODY_BYTES"] = "2048"
        cfg = load_config()
        self.assertEqual(cfg.port, 9911)
        self.assertEqual(cfg.max_body_bytes, 2048)
        self.assertTrue(cfg.auth_required)
        self.assertIn("almeezan-home", str(cfg.ledger_path))

    def test_invalid_numbers_fall_back(self) -> None:
        os.environ["ALMEEZAN_PORT"] = "not-a-number"
        cfg = load_config()
        self.assertEqual(cfg.port, 8787)


class MetricsTests(unittest.TestCase):
    def test_counters_and_percentiles(self) -> None:
        metrics = Metrics("almeezan", __version__)
        for _ in range(10):
            metrics.inc("http_requests_total")
        for value in range(1, 101):
            metrics.observe_ms(float(value))
        snapshot = metrics.snapshot()
        self.assertEqual(snapshot["counters"]["http_requests_total"], 10)
        self.assertEqual(snapshot["latency_ms"]["samples"], 100)
        self.assertGreaterEqual(snapshot["latency_ms"]["p95"], snapshot["latency_ms"]["p50"])
        self.assertGreaterEqual(snapshot["latency_ms"]["p99"], snapshot["latency_ms"]["p95"])
        self.assertEqual(snapshot["latency_ms"]["max"], 100.0)

    def test_empty_snapshot(self) -> None:
        snapshot = Metrics("almeezan", __version__).snapshot()
        self.assertEqual(snapshot["latency_ms"]["samples"], 0)
        self.assertEqual(snapshot["latency_ms"]["p99"], 0.0)


class ServiceTestBase(unittest.TestCase):
    api_key = ""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        tmp_path = Path(self._tmp.name)
        os.environ["ALMEEZAN_API_KEY"] = self.api_key
        os.environ["ALMEEZAN_LOG_DIR"] = str(tmp_path / "logs")
        self.server = create_server(host="127.0.0.1", port=0, ledger=tmp_path / "ledger.jsonl")
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        os.environ.pop("ALMEEZAN_API_KEY", None)
        os.environ.pop("ALMEEZAN_LOG_DIR", None)
        if Handler.logger is not None:
            for handler in list(Handler.logger.handlers):
                handler.close()
                Handler.logger.removeHandler(handler)
            Handler.logger._almeezan_configured = False  # type: ignore[attr-defined]
        Handler.logger = None
        self._tmp.cleanup()

    def request(self, path: str, payload: dict | None = None, headers: dict | None = None):
        url = f"http://127.0.0.1:{self.port}{path}"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(url, data=data, headers=headers or {})
        if data is not None:
            request.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))


class OpenServiceTests(ServiceTestBase):
    api_key = ""

    def test_health_reports_version(self) -> None:
        status, body = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["version"], __version__)
        self.assertFalse(body["auth_required"])

    def test_evaluate_and_metrics(self) -> None:
        payload = {
            "use_case": "test",
            "risk_level": "low",
            "prompt": "سؤال",
            "output": "جواب قصير",
            "evidence": [{"id": "e1", "title": "t", "text": "جواب قصير مدعوم"}],
        }
        status, body = self.request("/api/evaluate", payload)
        self.assertEqual(status, 200)
        self.assertIn(body["verdict"], {"PASS", "REVIEW", "BLOCK"})
        status, metrics = self.request("/api/metrics")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(metrics["counters"].get("http_requests_total", 0), 1)
        self.assertGreaterEqual(metrics["latency_ms"]["samples"], 1)


class AuthServiceTests(ServiceTestBase):
    api_key = "secret-key-42"

    def test_rejects_missing_key(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.request("/api/metrics")
        self.assertEqual(ctx.exception.code, 401)

    def test_accepts_valid_key(self) -> None:
        status, body = self.request("/api/metrics", headers={"X-API-Key": "secret-key-42"})
        self.assertEqual(status, 200)
        self.assertEqual(body["service"], "almeezan")

    def test_health_stays_open_for_probes(self) -> None:
        status, body = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["auth_required"])

    def test_oversized_body_rejected(self) -> None:
        big = {"output": "x" * (Handler.max_body_bytes + 10), "prompt": "p"}
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.request("/api/evaluate", big, headers={"X-API-Key": "secret-key-42"})
        self.assertEqual(ctx.exception.code, 413)


if __name__ == "__main__":
    unittest.main()
