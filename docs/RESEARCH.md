# بحث «الميزان»

## بحث محلي

من `C:\Users\FARHAN\AI_PROJECTS_REFERENCE\MASTER_REFERENCE.md` و`PROJECT_IDEAS.md`:

- «الصدى» منجز فعلاً في `C:\Projects\alsada`، وله قياس ورادار ونشر وتقارير.
- CarbonFlow لديه تقرير تدقيق أمني في `C:\Users\FARHAN\AI_PROJECTS_REFERENCE\REPORTS\CarbonFlow_Server_Audit_2026-07-03.md`.
- «الميزان» محفوظ كفكرة قوية غير منفذة محلياً: حَكَم مستقل يزن المصداقية، الخصوصية، السياسة، الإشراف، وسجل تدقيق.
- أقرب الكنوز الموجودة: بروكسي التعقيم، izaen، AEGIS ledger، RAG/Qdrant، وتعدد النماذج. لذلك تم تنفيذ نواة مستقلة بلا تبعيات لتصبح قابلة للدمج لاحقاً.

## بحث الويب

مصادر التصميم:

- NIST AI RMF يؤكد إدارة مخاطر الذكاء عبر الحوكمة والقياس والإدارة، وNIST AI 600-1 يضيف مخاطر GenAI مثل confabulation والخصوصية والاختبار قبل النشر.
  - https://www.nist.gov/itl/ai-risk-management-framework
  - https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
- EU AI Act Article 12 يتطلب تسجيل أحداث تلقائي يدعم التتبع ومراقبة التشغيل، وهذا أساس ledger.
  - https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-12
- EU AI Act Article 14 يركز على الإشراف البشري، فهم حدود النظام، تفسير المخرجات، وحق التجاوز/الإيقاف.
  - https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-14
- OWASP LLM Top 10 2025 يضع Prompt Injection، Sensitive Information Disclosure، Excessive Agency، وOverreliance ضمن مخاطر LLM المهمة.
  - https://owasp.org/www-project-top-10-for-large-language-model-applications/
  - https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- Ragas faithfulness يقيس اتساق الرد مع السياق المسترجع كنسبة الادعاءات المدعومة إلى إجمالي الادعاءات. تم تبني نسخة حتمية محلية من هذا المبدأ.
  - https://github.com/vibrantlabsai/ragas/blob/main/docs/concepts/metrics/available_metrics/faithfulness.md

## قرار التنفيذ

النسخة الأولى تبني طبقة حكم محلية حتمية:

1. تقسيم المخرَج إلى ادعاءات.
2. مطابقة الادعاءات مع الأدلة النصية محلياً.
3. كشف PII والأسرار في المخرَج.
4. كشف حقن الأوامر والمخاطر التشغيلية.
5. إصدار درجة وقرار عربي واضح.
6. ختم الحكم في سجل hash-chain.

هذا يعطي منتجاً عاملاً الآن، ويفتح الطريق لاحقاً لإضافة Qdrant/Ollama/Ed25519 دون إعادة بناء الهيكل.

