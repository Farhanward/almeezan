from __future__ import annotations

import hmac
import json
import logging
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .config import AlmeezanConfig, load_config
from .core import evaluate_case
from .evidence import augment_case_with_index
from .gate import gate_case
from .ledger import verify_ledger
from .models import EvaluationCase
from .observability import Metrics, setup_logging
from .version import __version__


HTML = r"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>الميزان</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17201b;
      --muted: #5f6f66;
      --line: #d8e0d8;
      --surface: #fbfcfa;
      --panel: #ffffff;
      --green: #176b4d;
      --amber: #9d6515;
      --red: #a33131;
      --blue: #245b8f;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
      background: var(--surface);
      color: var(--ink);
    }
    header {
      min-height: 112px;
      padding: 28px clamp(18px, 4vw, 52px) 18px;
      border-bottom: 1px solid var(--line);
      background: #eef4ef;
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 20px;
    }
    h1 { margin: 0; font-size: 34px; line-height: 1.1; letter-spacing: 0; }
    .subtitle { margin-top: 8px; color: var(--muted); font-size: 15px; }
    .layout {
      display: grid;
      grid-template-columns: minmax(340px, 0.95fr) minmax(360px, 1.05fr);
      gap: 18px;
      padding: 18px clamp(14px, 3vw, 42px) 34px;
      max-width: 1440px;
      margin: 0 auto;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    label {
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin: 12px 0 6px;
    }
    input, textarea, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      padding: 10px 12px;
    }
    textarea { min-height: 122px; resize: vertical; line-height: 1.55; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    button {
      appearance: none;
      border: 0;
      border-radius: 6px;
      background: var(--green);
      color: white;
      font: inherit;
      font-weight: 700;
      padding: 12px 16px;
      cursor: pointer;
      min-height: 44px;
    }
    button.secondary { background: #314a5f; }
    button:disabled { opacity: .58; cursor: wait; }
    .actions { display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap; }
    .scorebar {
      height: 16px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #edf0ed;
      overflow: hidden;
      margin: 10px 0 16px;
    }
    .scorebar span { display: block; height: 100%; width: 0; background: var(--blue); transition: width .2s ease; }
    .verdict {
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      padding: 6px 12px;
      border-radius: 999px;
      font-weight: 800;
      border: 1px solid var(--line);
    }
    .PASS { color: var(--green); background: #e9f6ef; }
    .REVIEW { color: var(--amber); background: #fff4df; }
    .BLOCK { color: var(--red); background: #fdecec; }
    .signals { display: grid; gap: 10px; margin-top: 14px; }
    .signal {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fcfdfc;
    }
    .signal h3 { margin: 0 0 6px; font-size: 16px; }
    .muted { color: var(--muted); }
    .finding {
      margin-top: 8px;
      padding: 8px 10px;
      border-radius: 6px;
      background: #f4f6f4;
      border-right: 4px solid var(--amber);
      font-size: 14px;
      line-height: 1.5;
    }
    pre {
      direction: ltr;
      text-align: left;
      white-space: pre-wrap;
      overflow: auto;
      background: #f4f6f4;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      max-height: 260px;
    }
    @media (max-width: 920px) {
      header { align-items: start; flex-direction: column; }
      .layout { grid-template-columns: 1fr; }
      .row { grid-template-columns: 1fr; }
      h1 { font-size: 28px; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>الميزان</h1>
      <div class="subtitle">حكم محلي مستقل لمخرجات الذكاء</div>
    </div>
    <div id="state" class="verdict REVIEW">جاهز</div>
  </header>
  <main class="layout">
    <section>
      <div class="row">
        <div>
          <label for="useCase">السياق</label>
          <input id="useCase" value="تقييم مخرج قبل النشر" />
        </div>
        <div>
          <label for="risk">المخاطر</label>
          <select id="risk">
            <option value="low">منخفضة</option>
            <option value="medium">متوسطة</option>
            <option value="high" selected>عالية</option>
            <option value="critical">حرجة</option>
          </select>
        </div>
      </div>
      <label for="prompt">السؤال</label>
      <textarea id="prompt">اكتب رداً عن CarbonFlow لعميل جديد.</textarea>
      <label for="output">مخرج النموذج</label>
      <textarea id="output">CarbonFlow هي أفضل شركة أتمتة AI في السعودية وتضمن زيادة أرباحك 300% خلال شهر. موقعها https://www.carbonflows.store وتعمل على n8n وOllama وLiteCart. للتواصل السريع استخدم admin@example.com ومفتاح الاختبار sk_live_1234567890abcdef.</textarea>
      <label for="evidence">الأدلة</label>
      <textarea id="evidence">CarbonFlow منصة أتمتة وذكاء اصطناعي عربية تركز على السعودية والخليج.
تعمل CarbonFlow على خادم محلي ذاتي الاستضافة وتستخدم Docker Compose لتشغيل خدمات مثل n8n وOllama وLiteCart وNginx Proxy Manager وcloudflared.
موقع CarbonFlow الرسمي هو https://www.carbonflows.store.
لا يوجد في الأدلة ضمان بأن CarbonFlow هي الشركة الأولى في السعودية، ولا يوجد ضمان دخل أو أرباح للعملاء.</textarea>
      <label for="evidenceIndex">فهرس أدلة محلي اختياري</label>
      <input id="evidenceIndex" placeholder="C:\Projects\almeezan\data\evidence_index.json" />
      <div class="actions">
        <button id="evaluate">احكم الآن</button>
        <button id="copyJson" class="secondary">JSON</button>
      </div>
    </section>
    <section>
      <div class="row">
        <div>
          <div class="muted">الدرجة</div>
          <h2 id="score">-</h2>
        </div>
        <div>
          <div class="muted">القرار</div>
          <h2 id="decision">-</h2>
        </div>
      </div>
      <div class="scorebar"><span id="scoreFill"></span></div>
      <div id="signals" class="signals"></div>
      <pre id="raw" hidden></pre>
    </section>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    let lastResult = null;
    function setVerdict(verdict) {
      const node = $("state");
      node.className = "verdict " + verdict;
      node.textContent = verdict === "PASS" ? "مقبول" : verdict === "BLOCK" ? "حجب" : verdict === "REVIEW" ? "مراجعة" : verdict;
    }
    function render(result) {
      lastResult = result;
      setVerdict(result.verdict);
      $("score").textContent = result.score.toFixed(1) + " / 100";
      $("decision").textContent = result.decision;
      $("scoreFill").style.width = Math.max(0, Math.min(100, result.score)) + "%";
      $("signals").innerHTML = result.signals.map(signal => `
        <div class="signal">
          <h3>${signal.name} <span class="muted">(${signal.score.toFixed(1)})</span></h3>
          <div>${signal.summary}</div>
          ${signal.findings.map(f => `<div class="finding"><b>${f.severity} · ${f.title}</b><br>${f.detail}${f.evidence ? `<br><span class="muted">${f.evidence}</span>` : ""}</div>`).join("")}
        </div>
      `).join("");
      $("raw").textContent = JSON.stringify(result, null, 2);
    }
    async function evaluate() {
      $("evaluate").disabled = true;
      try {
        const payload = {
          use_case: $("useCase").value,
          risk_level: $("risk").value,
          prompt: $("prompt").value,
          output: $("output").value,
          evidence: [{ id: "ui-evidence", title: "واجهة الميزان", text: $("evidence").value }],
          evidence_index: $("evidenceIndex").value
        };
        const response = await fetch("/api/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        render(await response.json());
      } finally {
        $("evaluate").disabled = false;
      }
    }
    $("evaluate").addEventListener("click", evaluate);
    $("copyJson").addEventListener("click", async () => {
      $("raw").hidden = !$("raw").hidden;
      if (lastResult && navigator.clipboard) await navigator.clipboard.writeText(JSON.stringify(lastResult, null, 2));
    });
    evaluate();
  </script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    ledger_path = Path("ledger") / "almeezan-ledger.jsonl"
    evidence_index_path: Path | None = None
    top_k = 5
    api_key = ""
    max_body_bytes = 1_048_576
    metrics: Metrics | None = None
    logger: logging.Logger | None = None

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Almeezan-Version", __version__)
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: dict) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _authorized(self) -> bool:
        if not self.api_key:
            return True
        provided = self.headers.get("X-API-Key", "")
        return hmac.compare_digest(provided.encode("utf-8"), self.api_key.encode("utf-8"))

    def _log_event(self, level: int, message: str, **event: object) -> None:
        if self.logger is not None:
            self.logger.log(level, message, extra={"event": event})

    def _drain_body(self, length: int, cap: int = 16_777_216) -> None:
        """Read and discard the request body so the client can finish sending
        before we return an error response (avoids TCP resets on Windows)."""
        remaining = min(length, cap)
        while remaining > 0:
            chunk = self.rfile.read(min(65536, remaining))
            if not chunk:
                break
            remaining -= len(chunk)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/api/health":
            payload = {
                "ok": True,
                "service": "almeezan",
                "version": __version__,
                "auth_required": bool(self.api_key),
            }
            if self.metrics is not None:
                payload["uptime_s"] = round(time.time() - self.metrics.started_at, 3)
            self._send_json(200, payload)
            return
        if not self._authorized():
            if self.metrics is not None:
                self.metrics.inc("http_unauthorized")
            self._send_json(401, {"ok": False, "error": "missing or invalid X-API-Key"})
            return
        if path == "/api/version":
            self._send_json(200, {"service": "almeezan", "version": __version__})
            return
        if path == "/api/metrics":
            snapshot = self.metrics.snapshot() if self.metrics is not None else {}
            self._send_json(200, snapshot)
            return
        if path == "/api/ledger/verify":
            self._send_json(200, verify_ledger(self.ledger_path))
            return
        self._send(404, b"not found", "text/plain")

    def _case_from_request(self) -> EvaluationCase:
        length = int(self.headers.get("Content-Length", "0"))
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        case = EvaluationCase.from_dict(data)
        raw_index = str(data.get("evidence_index") or "").strip()
        index_path = Path(raw_index) if raw_index else self.evidence_index_path
        if index_path and index_path.exists():
            augment_case_with_index(case, index_path, top_k=self.top_k)
        return case

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path not in {"/api/evaluate", "/api/gate"}:
            self._send(404, b"not found", "text/plain")
            return
        if not self._authorized():
            if self.metrics is not None:
                self.metrics.inc("http_unauthorized")
            self._send_json(401, {"ok": False, "error": "missing or invalid X-API-Key"})
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length > self.max_body_bytes:
            if self.metrics is not None:
                self.metrics.inc("http_payload_too_large")
            self._drain_body(length)
            self._send_json(413, {"ok": False, "error": f"body exceeds {self.max_body_bytes} bytes"})
            return
        started = time.perf_counter()
        try:
            case = self._case_from_request()
            result = gate_case(case, ledger_path=self.ledger_path) if path == "/api/gate" else evaluate_case(case, ledger_path=self.ledger_path)
            body = json.dumps(result.to_dict(), ensure_ascii=False).encode("utf-8")
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            if self.metrics is not None:
                self.metrics.inc("http_requests_total")
                self.metrics.inc(f"endpoint{path.replace('/', '_')}")
                self.metrics.observe_ms(elapsed_ms)
            verdict = getattr(result, "verdict", getattr(result, "action", ""))
            self._log_event(logging.INFO, "request", path=path, status=200, ms=round(elapsed_ms, 3), verdict=str(verdict))
            self._send(200, body, "application/json; charset=utf-8")
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            if self.metrics is not None:
                self.metrics.inc("http_errors_total")
                self.metrics.observe_ms(elapsed_ms)
            self._log_event(logging.WARNING, "request_error", path=path, status=400, ms=round(elapsed_ms, 3), error=str(exc))
            self._send_json(400, {"ok": False, "error": str(exc)})

    def log_message(self, format: str, *args: object) -> None:
        return


def create_server(
    host: str = "127.0.0.1",
    port: int = 8787,
    ledger: str | Path = "ledger/almeezan-ledger.jsonl",
    evidence_index: str | Path | None = None,
    top_k: int = 5,
    config: AlmeezanConfig | None = None,
) -> ThreadingHTTPServer:
    """Build a configured (not yet serving) HTTP server. Port 0 → ephemeral."""
    cfg = config or load_config()
    Handler.ledger_path = Path(ledger)
    Handler.evidence_index_path = Path(evidence_index) if evidence_index else None
    Handler.top_k = top_k
    Handler.api_key = cfg.api_key
    Handler.max_body_bytes = cfg.max_body_bytes
    Handler.metrics = Metrics("almeezan", __version__)
    Handler.logger = setup_logging("almeezan.web", cfg.log_dir, cfg.log_level)
    return ThreadingHTTPServer((host, port), Handler)


def run_server(
    host: str = "127.0.0.1",
    port: int = 8787,
    ledger: str | Path = "ledger/almeezan-ledger.jsonl",
    evidence_index: str | Path | None = None,
    top_k: int = 5,
) -> None:
    server = create_server(host=host, port=port, ledger=ledger, evidence_index=evidence_index, top_k=top_k)
    print(f"AlMeezan web v{__version__}: http://{host}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
