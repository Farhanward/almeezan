# الميزان — حَكَم محلي لمخرجات الذكاء

`almeezan` هو تنفيذ أول كامل لفكرة «الميزان»: طبقة محلية تفحص مخرجات الذكاء قبل استخدامها، وتصدر قراراً قابلاً للمراجعة:

- هل المخرَج مدعوم بالأدلة أم فيه هلوسة؟
- هل يسرّب بريدًا، هاتفًا، مفاتيح API، بطاقات، أو أسرارًا؟
- هل يحتوي آثار حقن أوامر، طلب كشف system prompt، أو تعليمات خطرة؟
- هل يحتاج مراجعة بشرية أو إيقاف؟
- هل حُفظ الحكم في سجل تدقيق لا يقبل العبث بصمت؟

لا يحتاج مفاتيح API ولا خدمات خارجية. يعمل بـ Python القياسي فقط.

## التشغيل السريع

```powershell
cd C:\Projects\almeezan
python -m almeezan.cli evaluate --input examples\sample_case.json --out reports\sample_report.md
```

فتح الواجهة المحلية:

```powershell
cd C:\Projects\almeezan
python -m almeezan.cli web --port 8787
```

ثم افتح:

```text
http://127.0.0.1:8787
```

API محلي:

- `GET /api/health` (مفتوح دائماً — للـ probes)
- `GET /api/version`
- `GET /api/metrics` (عدادات + p50/p95/p99)
- `POST /api/evaluate`
- `POST /api/gate`
- `GET /api/ledger/verify`

## التشغيل المؤسسي (Enterprise)

- **تهيئة عبر البيئة**: كل الإعدادات من متغيرات `ALMEEZAN_*` (انظر `docs/OPERATIONS.md`).
- **مصادقة**: اضبط `ALMEEZAN_API_KEY` فيصبح كل `/api/*` (عدا health) بمفتاح `X-API-Key`.
- **سجلات JSON منظمة**: `logs\almeezan.web.jsonl` بتدوير تلقائي.
- **حدود حماية**: حجم الطلب الأقصى `ALMEEZAN_MAX_BODY_BYTES` (افتراضي 1MB → 413).
- **دليل التشغيل**: `docs/OPERATIONS.md` · **سجل التغييرات**: `CHANGELOG.md`.

ملاحظة API: استخدم `evidence` كنص مباشر، أو أرسل مسارات أدلة مطلقة. مسارات `evidence_paths` النسبية مصممة أساساً لملفات CLI.

## أوامر

```powershell
python -m almeezan.cli evaluate --input examples\sample_case.json --format md
python -m almeezan.cli evaluate --input examples\sample_case.json --format json
python -m almeezan.cli gate --input examples\sample_case.json --format json
python -m almeezan.cli index --source examples --out data\evidence_index.json
python -m almeezan.cli evaluate --input examples\sample_case.json --evidence-index data\evidence_index.json
python -m almeezan.cli batch --input-dir examples\batch --out-dir reports\batch --evidence-index data\evidence_index.json
python -m almeezan.cli verify-ledger
python -m almeezan.cli web --port 8787 --evidence-index data\evidence_index.json
```

تشغيل الاختبارات:

```powershell
python -m unittest discover -s tests -v
```

## صيغة ملف الإدخال

```json
{
  "use_case": "دعم عملاء",
  "model": "example-model",
  "risk_level": "high",
  "prompt": "سؤال المستخدم",
  "output": "إجابة النموذج المراد فحصها",
  "evidence": [
    {
      "id": "source-1",
      "title": "مصدر داخلي",
      "text": "الأدلة المعتمدة"
    }
  ],
  "metadata": {
    "owner": "CarbonFlow"
  }
}
```

يمكن أيضاً استخدام `evidence_paths` لقراءة ملفات أدلة محلية.

## بنية الحكم

القرار النهائي أحد ثلاثة:

- `PASS`: المخرَج مقبول.
- `REVIEW`: لا يُمنع، لكنه يحتاج مراجعة بشرية.
- `BLOCK`: يوصى بحجبه أو إيقاف استخدامه.

يحسب الميزان الدرجة من أربع طبقات:

- الاتساق مع الأدلة.
- الخصوصية والأسرار.
- حقن الأوامر والمخاطر التشغيلية.
- قابلية الإشراف البشري.

## سجل التدقيق

كل تقييم يحفظ إدخالاً في:

```text
ledger\almeezan-ledger.jsonl
```

كل إدخال يحتوي hash للحمولة وhash للإدخال السابق وHMAC محلي. يمكن التحقق:

```powershell
python -m almeezan.cli verify-ledger
```

## فهرسة الأدلة

يبني الميزان فهرساً محلياً من ملفات Markdown/Text/JSON/YAML/HTML/CSV، ثم يسترجع أفضل المقاطع تلقائياً لكل مخرج:

```powershell
python -m almeezan.cli index --source C:\Users\FARHAN\AI_PROJECTS_REFERENCE --out data\farhan_reference_index.json
python -m almeezan.cli evaluate --input examples\sample_case.json --evidence-index data\farhan_reference_index.json --top-k 6
```

## التشغيل الجماعي

ضع ملفات JSON في مجلد واحد ثم شغّل:

```powershell
python -m almeezan.cli batch --input-dir examples\batch --out-dir reports\batch --evidence-index data\evidence_index.json
```

ينتج:

- تقرير Markdown لكل حالة.
- JSON لكل حكم.
- `batch_summary.md` و`batch_summary.json`.

## بيانات اختبار كبيرة

تم تجهيز مجموعة Databricks Dolly 15k محلياً لاختبارات واسعة:

```powershell
python tools\download_dolly_15k.py
python tools\smoke_dolly_15k.py
```

المخرجات:

- `data\external\databricks-dolly-15k\databricks-dolly-15k.jsonl`
- `data\external\databricks-dolly-15k\databricks-dolly-15k.almeezan.jsonl`
- `reports\dolly_15k_smoke_summary.md`

## بوابة الإنتاج

أمر `gate` مناسب للربط قبل النشر أو قبل الرد على العميل:

```powershell
python -m almeezan.cli gate --input examples\sample_case.json --evidence-index data\evidence_index.json --out reports\gate_sample.json
```

يرجع:

- `allow`: المخرج يمر كما هو.
- `allow_after_rewrite`: المخرج مر بعد تنقيح الأسرار وحذف الجمل غير المدعومة.
- `review_after_rewrite`: النسخة المنقحة أفضل، لكنها تحتاج مراجعة بشرية.
- `block`: لا يمر حتى بعد التنقيح.

## الملفات المهمة

- `almeezan\core.py`: محرك التقييم.
- `almeezan\claims.py`: قياس دعم الادعاءات بالأدلة.
- `almeezan\pii.py`: كشف PII والأسرار.
- `almeezan\policy.py`: حقن أوامر ومخاطر تشغيلية.
- `almeezan\ledger.py`: سجل تدقيق hash-chain.
- `almeezan\evidence.py`: فهرسة واسترجاع الأدلة محلياً.
- `almeezan\batch.py`: تشغيل جماعي وتقارير تنفيذية.
- `almeezan\gate.py`: بوابة تنقيح/حجب/تمرير جاهزة للربط.
- `almeezan\web.py`: واجهة محلية RTL.
- `docs\RESEARCH.md`: خلاصة البحث المحلي والويب.

## آخر نتائج

- الاختبارات الذاتية: 23/23 ناجحة (منها 11 اختبار enterprise).
- Ledger: verified.

## تحسينات إنتاجية 2026-07-04

- في السياقات عالية/حرجة المخاطر، لا يسمح الميزان بتمرير إجابة بلا أدلة فعلية حتى لو كانت الإجابة القصيرة مستخرجة من خيارات السؤال.
- أضيفت إشارة `HIGH_RISK_NO_EVIDENCE` في طبقة الإشراف البشري، وتعد critical حتى لا تختفي داخل الدرجة الإجمالية.
