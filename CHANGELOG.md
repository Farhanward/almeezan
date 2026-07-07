# Changelog — almeezan

## 1.0.0 — 2026-07-05 (الترقية المؤسسية)

- **Config مركزي عبر البيئة**: `almeezan/config.py` — كل مسارات/منافذ/حدود التشغيل من env vars (`ALMEEZAN_*`) بلا مسارات صلبة.
- **Observability**: `almeezan/observability.py` — سجلات JSON منظمة بتدوير تلقائي + عدادات وp50/p95/p99 لكل طلب.
- **تقوية خدمة HTTP**: مصادقة `X-API-Key` اختيارية (مقارنة constant-time)، حد حجم الطلب (413)، `/api/metrics`، `/api/version`، إثراء `/api/health` بالإصدار وزمن التشغيل، وترويسة `X-Almeezan-Version`.
- **تغليف**: `pyproject.toml` كامل مع `almeezan` console entry point وأمر `version`.
- **توثيق تشغيل**: `docs/OPERATIONS.md` (runbook: تهيئة، فحص، نسخ احتياطي، حوادث، ترقية).
- **اختبارات enterprise**: `tests/test_enterprise.py` — config من البيئة، metrics، auth 401/200، health المفتوح، 413 للحمولات الكبيرة، خادم حقيقي على منفذ ephemeral.

## 0.1.0 — 2026-07-03/04

- المنتج الأولي: محرك تقييم بأربع إشارات، بوابة gate، فهرسة أدلة، سجل hash-chain/HMAC، واجهة RTL، batch، وبيانات Dolly 15k.
- تحسين إنتاجي: إشارة `HIGH_RISK_NO_EVIDENCE` تمنع تمرير إجابات بلا أدلة في السياقات الحرجة.
