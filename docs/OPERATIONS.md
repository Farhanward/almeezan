# دليل تشغيل الميزان (Operations Runbook)

هذا الدليل موجه لمشغّل النظام في بيئة إنتاج محلية أو خادم داخلي.

## 1) التهيئة عبر متغيرات البيئة

| المتغير | الافتراضي | الوظيفة |
|---|---|---|
| `ALMEEZAN_HOME` | جذر المشروع | مجلد الحالة (ledger/logs) |
| `ALMEEZAN_LEDGER` | `<home>\ledger\almeezan-ledger.jsonl` | ملف سجل التدقيق |
| `ALMEEZAN_SECRET` | `<home>\ledger\.almeezan-secret` | مفتاح HMAC للسجل |
| `ALMEEZAN_API_KEY` | (فارغ = بلا مصادقة) | إن ضُبط: كل `/api/*` يتطلب `X-API-Key` |
| `ALMEEZAN_HOST` / `ALMEEZAN_PORT` | `127.0.0.1` / `8787` | عنوان الخدمة |
| `ALMEEZAN_MAX_BODY_BYTES` | `1048576` | حد حجم الطلب (413 عند التجاوز) |
| `ALMEEZAN_LOG_DIR` | `<home>\logs` | مجلد سجلات JSON |
| `ALMEEZAN_LOG_LEVEL` | `INFO` | مستوى السجل |

ملاحظة: `/api/health` يبقى مفتوحاً دائماً (لفحوصات الجاهزية)، وكل ما عداه يخضع للمفتاح عند ضبطه.

## 2) تشغيل الخدمة

```powershell
$env:ALMEEZAN_API_KEY = "ضع-مفتاحاً-قوياً"
python -m almeezan.cli web --host 127.0.0.1 --port 8787
```

## 3) نقاط الفحص

- `GET /api/health` → `{ok, service, version, uptime_s, auth_required}` — مفتوح دائماً.
- `GET /api/version` → إصدار الخدمة.
- `GET /api/metrics` → عدادات + p50/p95/p99 زمن المعالجة.
- `GET /api/ledger/verify` → سلامة سلسلة السجل.

## 4) السجلات

سجلات JSON سطرية في `logs\almeezan.web.jsonl` (تدوير تلقائي 5MB × 3 نسخ).
كل طلب: `{ts, level, message, path, status, ms, verdict}`.

## 5) النسخ الاحتياطي

انسخ دورياً:
- `ledger\almeezan-ledger.jsonl` (سجل الأحكام).
- `ledger\.almeezan-secret` (بدونه لا يمكن التحقق من الأختام) — خزّنه في مكان منفصل وآمن.

## 6) الحوادث الشائعة

| العرض | السبب المرجح | العلاج |
|---|---|---|
| `401` لكل الطلبات | مفتاح API خاطئ لدى العميل | تحقق من `X-API-Key` وطابقه مع `ALMEEZAN_API_KEY` |
| `413` | حمولة أكبر من الحد | ارفع `ALMEEZAN_MAX_BODY_BYTES` أو قسّم الطلب |
| `verify-ledger` يفشل | عبث أو تحرير يدوي للسجل | أوقف الكتابة، احتفظ بالنسخة للفحص الجنائي، استرجع آخر نسخة سليمة |
| بطء p99 | فهرس أدلة ضخم لكل طلب | ابنِ الفهرس مرة واحدة ومرّره عبر `--evidence-index` |

## 7) الترقية

1. أوقف الخدمة.
2. حدّث الكود ثم `python -m unittest discover -s tests -v` (يجب أن تنجح كلها).
3. `python -m almeezan.cli verify-ledger` للتأكد من سلامة السجل.
4. أعد التشغيل وتحقق من `/api/health`.
