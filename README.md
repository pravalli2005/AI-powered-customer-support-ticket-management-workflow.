# AI-Powered Customer Support Ticket Workflow & SLA Operations Platform

An enterprise-ready, intelligent support operations system that converts unstructured customer conversations into normalized, prioritized, and routed support tickets with dynamic business-hours SLA monitoring, deduplication, incident clustering, knowledge base auto-resolution, and human-in-the-loop verification.

---

## 🌟 Key Capabilities & Architecture

1. **AI Conversation Parser & NER**:
   - Extracts Customer identity, Order reference, Product info, Category, Sentiment, Severity, and Evidence.
   - **Confidence Scoring & Human-in-the-Loop**: Returns granular extraction confidence. If overall confidence < 70%, flags `NEEDS_REVIEW` for supervisor triage.
   - **Smart Contextual Prompts**: Generates targeted questions for missing mandatory fields (e.g. asking for photos & order number for damaged goods).
   - **Multi-Issue Splitting**: Automatically splits compound messages (*"Late package AND broken login link"*) into separate domain tickets.

2. **Deduplication & Master Incident Correlation**:
   - Prevents duplicate flurry tickets from the same customer within configured time windows.
   - Clusters mass platform outages (e.g. 50+ users reporting payment gateway failures) under a parent Master Incident with elevated `CRITICAL` priority.

3. **High-Precision SLA Engine**:
   - Excludes weekends (e.g., Saturday/Sunday) and configurable holiday calendars.
   - Restricts SLA clock to daily business shifts (e.g., Mon–Fri 09:00–18:00).
   - **SLA Pause & Resume**: Automatically pauses the clock when waiting for customer input (`WAITING_FOR_CUSTOMER`), and resumes extending the deadline when the customer replies.
   - **75% SLA Warning Threshold**: Emits warning notifications before breach.
   - **Multi-Tier Escalation**: Auto-escalates on breach (Agent &rarr; Team Lead &rarr; Support Manager).
   - **Dynamic Runtime Mutation**: Recalculates remaining deadlines mid-flight if SLA targets are compressed (e.g., 8h &rarr; 4h) or new holidays are added.

4. **Configurable Multi-Factor Priority Engine**:
   - Computes normalized priority scores:
     $$\text{Priority Score} = \frac{\text{Sev} \times W_{\text{sev}} + \text{Sent} \times W_{\text{sent}} + \text{Impact} \times W_{\text{imp}} + \text{Wait} \times W_{\text{wait}} + \text{SLARisk} \times W_{\text{sla}}}{\sum W}$$
   - Administrative weights are reconfigurable dynamically at runtime.

5. **Knowledge Base Self-Service & Agent Assistance**:
   - Matches FAQs (e.g. password reset guide) and resolves tickets instantly without human agent touch.
   - Generates empathetic, context-aware AI suggested responses for human agents.

6. **Intelligent Routing & Fallbacks**:
   - Matches agent skills, availability, and capacity limits.
   - Supports load-balanced distribution and automatic fallback to backup teams or unassigned queues.

7. **PII Masked Handoff**:
   - Redacts credit card numbers (`****-****-****-4444`), phone numbers (`********3210`), and email addresses (`r****@corp.com`) during inter-team escalation.

---

## 🧪 Hidden-Test Scenarios (HT-01 to HT-08)

All 8 hidden test scenarios are implemented and validated:

| Test ID | Scenario | Verification Focus | Status |
|---|---|---|---|
| **HT-01** | Duplicate Ticket Flurry | Merges rapid follow-ups into existing ticket | ✅ PASS |
| **HT-02** | Unavailable Teams Fallback | Routes to backup team / unassigned queue when primary team is full or offline | ✅ PASS |
| **HT-03** | Weekend Boundary SLA | Friday 17:30 arrival with 8h SLA lands strictly on Monday 16:30 | ✅ PASS |
| **HT-04** | Runtime Holiday Injection | Adding Monday holiday mid-flight pushes deadline to Tuesday 16:30 | ✅ PASS |
| **HT-05** | Runtime SLA Compression | Shortening SLA from 8h to 4h when 5h elapsed triggers immediate breach & L1 escalation | ✅ PASS |
| **HT-06** | Missing Mandatory Info | Enters `WAITING_FOR_CUSTOMER` on missing order ID; resumes on reply | ✅ PASS |
| **HT-07** | Multi-Issue & Mass Incident | Splits compound issues; clusters mass outages under Master Incident | ✅ PASS |
| **HT-08** | Masked Handoff Redaction | Redacts credit card, phone, email in cross-team handoff payloads | ✅ PASS |

---

## 🚀 Running the Automated Tests

To run the complete automated test suite (14 unit tests covering both hidden scenarios and advanced features):

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Output:
```text
test_ai_suggested_response ... ok
test_confidence_and_human_in_the_loop ... ok
test_configurable_priority_weights ... ok
test_knowledge_base_auto_resolution ... ok
test_sla_pause_and_resume ... ok
test_smart_missing_question_generation ... ok
test_ht01_duplicate_ticket_flurry ... ok
test_ht02_unavailable_team_and_skills_fallback ... ok
test_ht03_weekend_boundary_and_after_hours_sla ... ok
test_ht04_runtime_holiday_injection ... ok
test_ht05_runtime_sla_compression ... ok
test_ht06_missing_mandatory_information ... ok
test_ht07_multi_issue_splitting_and_mass_incident ... ok
test_ht08_masked_handoff_pii_redaction ... ok

----------------------------------------------------------------------
Ran 14 tests in 0.005s

OK
```

---

## 🖥️ Interactive Web Studio & Dashboard

To launch or preview the interactive visual studio:
1. Run `python app.py` (or open **[http://localhost:8000](http://localhost:8000)** if server is running).
2. The dashboard features:
   - **Executive KPI Cards**: Active tickets, SLA compliance rate, duplicates merged, KB auto-resolved, and CSAT rating.
   - **AI Confidence Gauge & Human-in-the-Loop flag**
   - **Dynamic Business-Hours SLA Progress Bar** with 75% warning line and breach states.
   - **AI Agent Suggested Responses** ready for copy/send.
   - **Interactive Hidden-Scenario Triggers** (HT-01 through HT-08).

---

## 📂 Repository Structure

```text
├── app.py                             # Main CLI demo runner & Web Studio server
├── docs/
│   └── workflow_refinement_spec.md    # Complete architectural specification & formal JSON Schema
├── src/
│   ├── models/
│   │   └── ticket.py                  # Domain data model, PII masking, lifecycle states, pause/resume
│   ├── sla/
│   │   └── engine.py                  # SLA engine with business hours, holidays, and dynamic recalculation
│   ├── priority/
│   │   └── engine.py                  # Configurable weighted priority engine
│   ├── routing/
│   │   └── engine.py                  # Skills-based load-balanced routing & fallbacks
│   ├── dedup/
│   │   └── engine.py                  # Duplicate flurry detection & incident correlation
│   ├── parser/
│   │   └── engine.py                  # NLP entity extraction, confidence scoring & multi-issue splitter
│   └── kb/
│       └── engine.py                  # Knowledge base auto-resolution & AI suggested responses
├── tests/
│   ├── test_hidden_scenarios.py       # 8 unit tests for evaluator hidden scenarios
│   └── test_advanced_features.py       # 6 unit tests for advanced platform capabilities
└── web/
    ├── index.html                     # Visual Studio Web UI with KPI cards & interactive controls
    ├── styles.css                     # Glassmorphic dark-mode styling
    └── app.js                         # Interactive simulation & client logic
```
