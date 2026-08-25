Readme · MD
# Aster & Row — RAG Support Agent
 
A small AI customer-support agent for **Aster & Row**, a fictional ecommerce company selling bags, drinkware, and travel accessories. Built for the *AI Agent Intern Take-Home: Build a Reliable RAG Support Agent*.
 
The agent answers company-policy questions using a retrieval-augmented pipeline over the supplied knowledge base, and answers order-status questions using a separate, sanitized lookup over the supplied mock order data. The brief for this assignment explicitly rewards a **small, reliable system over a broad one that only works in a demo** — this implementation is scoped accordingly.
 
---
# Screenshots

![alt text](<Screenshot 2026-08-25 221734.png>) ![alt text](<Screenshot 2026-08-25 211435.png>) ![alt text](<Screenshot 2026-08-25 211335.png>)



## 1. What's actually implemented
 
Being direct about scope, since the assignment scores reliability over breadth:
 
| Capability | Status |
|---|---|
| RAG over `knowledge-base/*.md` (chunk, embed, retrieve top-k) | ✅ Implemented |
| Order lookup with ID normalization | ✅ Implemented |
| Field allowlisting / privacy protection on orders | ✅ Implemented |
| Stale delivery info suppressed for cancelled/returned orders | ✅ Implemented |
| Unsupported-action detection (cancel/refund/address-change) | ✅ Implemented, keyword-based |
| Streamlit chat interface with source display | ✅ Implemented |
| Multi-turn order-ID carryover (scans prior messages) | ✅ Implemented, basic |
| History-aware retrieval for knowledge-base follow-ups | ⚠️ Not implemented — each knowledge question is retrieved independently, with no query rewriting from prior turns |
| Source-authority precedence (current vs. legacy docs) | ⚠️ Not implemented — retrieval is plain vector similarity with no metadata-based ranking; the prompt asks the model to prefer current sources, but nothing in the pipeline enforces it |
| Automated case-by-case evaluation grading | ⚠️ Not implemented — `evaluate.py` runs 3 hardcoded order-safety assertions and *lists* the custom cases, but does not yet execute the agent against each case or grade `must_include` / `must_not_include` / `handoff` fields |
| Structured logging / observability | ⚠️ Not implemented |
| `requirements.txt`, `.env.example` | ⚠️ Not present in this snapshot — see [Setup](#4-setup) |
 
This section exists so a reviewer doesn't have to reverse-engineer the gap between the assignment spec and the code — it's stated up front instead.
 
---
 
## 2. Architecture
 
```
                     User (Streamlit chat)
                              |
                              v
                          app.py
                              |
              +---------------+---------------+
              |               |                |
     unsupported-action   order question   knowledge question
       (keyword check)    (regex + orders.py)  (rag.py)
              |               |                |
              v               v                v
        canned refusal   get_order()      search_knowledge_base()
        + handoff copy    safe_order()          |
                              |                  v
                              v            FAISS similarity search
                        Groq (order prompt)      |
                                                  v
                                          Groq (knowledge prompt)
                                                  |
                                                  v
                                          Answer + source filenames
```
 
`app.py` routes each incoming message with simple keyword/regex checks, in this order:
 
1. **Unsupported action?** (`cancel`, `refund`, `change address`, etc.) → canned refusal, no LLM call, no order lookup.
2. **Order question?** (an `ORD-\d+` pattern in the message, or words like "tracking"/"arrive"/"shipped") → extract the order ID (falling back to scanning earlier messages in the session if the current message doesn't contain one) → `orders.py` → Groq.
3. **Otherwise** → treated as a knowledge-base question → `rag.py` → Groq.
The full order dataset is never sent to the model — only the single sanitized order object returned by `safe_order()`.
 
---
 
## 3. Technology stack
 
| Component | Choice |
|---|---|
| Language | Python |
| LLM provider | Groq |
| Model | `openai/gpt-oss-20b`, `temperature=0` |
| Orchestration | LangChain (`langchain-groq`, `langchain-core`) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` via `langchain-huggingface` |
| Vector store | FAISS (local, on-disk) |
| Interface | Streamlit |
| Order data | JSON, read directly (no DB) |
 
**Why Groq / `gpt-oss-20b`:** fast inference, low cost, enough capability for grounded QA at `temperature=0` for deterministic-ish output.
 
**Why `all-MiniLM-L6-v2`:** runs locally, no embedding API/key needed, more than adequate for the size of the supplied knowledge base.
 
**Why FAISS:** the assignment explicitly says a production vector database isn't required. FAISS is local, free, and trivial to reproduce for a corpus this small.
 
---
 
## 4. Setup
 
### Requirements
- Python 3.10+
- A Groq API key ([console.groq.com](https://console.groq.com))
### Install
 
```bash
git clone https://github.com/anantgarg/ai-agent-intern-test
cd ai-agent-intern-test
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
 
> **Note:** a `requirements.txt` isn't included in this snapshot of the repo. At minimum you'll need:
> ```
> streamlit
> python-dotenv
> langchain-core
> langchain-community
> langchain-groq
> langchain-huggingface
> langchain-text-splitters
> faiss-cpu
> sentence-transformers
> pytest
> ```
> Pin versions once you generate a real `requirements.txt` (`pip freeze > requirements.txt`) from your working environment.
 
### Configure environment
 
Create a `.env` file in the project root:
 
```
GROQ_API_KEY=your_groq_api_key
```
 
> An `.env.example` with this same key name (no real value) should be committed alongside it. Not yet present in this snapshot — add before final submission, since the assignment requires it.
 
### Build the FAISS index
 
```bash
python ingest.py
```
 
This loads every `.md` file in `knowledge-base/`, splits it (`chunk_size=1000`, `chunk_overlap=200`), embeds the chunks, and writes the index to `storage/faiss/`. Re-run this any time the knowledge base changes — the app reads a pre-built index, it doesn't ingest on startup.
 
### Run the app
 
```bash
streamlit run app.py
```
 
### Run tests
 
```bash
python -m pytest -v
```
 
### Run the evaluation script
 
```bash
python evaluate.py
```
 
This currently runs three deterministic order-safety checks directly and prints the list of custom cases from `evaluation/custom-cases.json`; see [Known Limitations](#8-known-limitations) for what it doesn't yet do.
 
---
 
## 5. Order lookup
 
`orders.py` exposes two functions:
 
- **`get_order(order_id)`** — strips whitespace, uppercases, validates against `ORD-\d+`, and looks up the order in `data/orders.json`. Returns `None` for anything malformed or not found — the caller doesn't need to guess why.
- **`safe_order(order)`** — copies only an allowlisted set of fields (`order_id`, `status`, `status_updated_at`, `placed_at`, `shipped_at`, `delivered_at`, `estimated_delivery`, `carrier`, `tracking_number`). Anything not on that list — customer name, email, shipping address, internal notes, risk score — is dropped by construction, not by exclusion, so a new sensitive field added to `orders.json` later doesn't leak by default.
For orders with `status` of `cancelled` or `returned`, `safe_order()` additionally strips `estimated_delivery`, `shipped_at`, `delivered_at`, `carrier`, and `tracking_number` — so the model physically cannot present stale delivery info as current, since it isn't in the payload it receives.
 
`app.py` never sends the model an order ID it hasn't independently looked up — the ID is extracted with `find_order_id()` (regex on the message, falling back to scanning prior session messages), then passed to `get_order()`. The model only ever sees the sanitized result.
 
---
 
## 6. Multi-turn behavior
 
Session history persists in `st.session_state.messages` for the lifetime of the Streamlit session.
 
**Order follow-ups** ("Where is ORD-1007?" → "When will it arrive?") work today: if the current message has no order ID, `app.py` scans backward through the session history for the most recent one and reuses it.
 
**Knowledge-base follow-ups** ("Do you ship internationally?" → "What about Canada?") are **not** specifically handled — each knowledge-base question is sent to `search_knowledge_base()` independently, with no rewriting or context injection from prior turns. A short follow-up like "What about Canada?" is retrieved on its own text, which may or may not surface the right passage depending on how much lexical overlap it has with the relevant document. This is a known gap, not a hidden one — see [Known Limitations](#8-known-limitations).
 
---
 
## 7. Bug diary
 
### Bug 1 — Broken import in `test_orders.py`
**Reproduction:** `python -m pytest -v` fails to collect `tests/test_orders.py`.
**Root cause:** `test_orders.py` imports `order_lookup` and `sanitize_order` from `orders.py`, but `orders.py` defines `get_order` and `safe_order`. It looks like an earlier draft used different function names and `orders.py` was refactored without updating this test file.
**Status:** Documented here rather than fixed, at the author's direction. `test_agent.py` in the same test suite imports the correct names and covers the same behavior (lowercase ID, unknown order, whitespace, private-field stripping, invalid ID), so coverage isn't actually lost — but `pytest -v` run as a whole will report a collection error until `test_orders.py` is either fixed or removed.
**Regression test:** N/A until fixed — flagging here so it isn't mistaken for a passing suite.
 
### Bug 2 — Lowercase / whitespace order IDs
**Reproduction:** `ord-1007` or `  ORD-1007  ` failed to match the stored `ORD-1007`.
**Root cause:** input was compared directly against the stored order ID without normalization.
**Fix:** `get_order()` calls `.strip().upper()` before lookup and validation.
**Regression test:** `test_agent.py::test_order_lookup`, `test_agent.py::test_order_id_whitespace`.
 
### Bug 3 — Unknown or malformed order IDs
**Reproduction:** `ORD-9999` (well-formed but nonexistent) and `hello` (malformed) both needed safe handling.
**Root cause:** without an explicit regex gate, a malformed ID could either raise an exception or silently fall through to a "not found" state indistinguishable from a real lookup miss.
**Fix:** `get_order()` regex-validates the format (`ORD-\d+`) before searching, and returns `None` uniformly for "malformed" and "not found" — the caller in `app.py` reports "couldn't find an order with ID X" either way rather than distinguishing invalid input from a genuine miss.
**Regression test:** `test_agent.py::test_unknown_order`, `test_agent.py::test_invalid_order_id`.
 
### Bug 4 — Stale delivery info on cancelled/returned orders
**Reproduction:** an order with `status: cancelled` still had a populated `estimated_delivery` field in the source data, which could otherwise get relayed as if the order were still in transit.
**Root cause:** `safe_order()` originally forwarded every allowlisted field regardless of order status.
**Fix:** added a status check that strips `estimated_delivery`, `shipped_at`, `delivered_at`, `carrier`, and `tracking_number` whenever `status` is `cancelled` or `returned`, so the model never receives them for those orders.
**Regression test:** covered conceptually by `custom-cases.json`'s `returned-order` case (asserts a specific stale date string is absent from the response), though `evaluate.py` doesn't yet execute this case against the live agent — see [Known Limitations](#8-known-limitations).
 
### Bug 5 — Lost order context on follow-up questions
**Reproduction:** "Where is ORD-1007?" followed by "When will it arrive?" — the second message has no order ID in it.
**Root cause:** the original routing only checked the current message for an `ORD-\d+` pattern.
**Fix:** if the current message has no order ID, `app.py` walks `st.session_state.messages` in reverse and reuses the most recent one found.
**Regression test:** not yet automated — currently verified manually in the Streamlit UI. Worth adding as an explicit evaluation case.
 
---
 
## 8. Evaluation results
 
![alt text](image.png)
---
 
---
 
## 9. Project structure (current)
 
```
ai-agent-intern-test/
├── README.md
├── app.py
├── orders.py
├── rag.py
├── ingest.py
├── evaluate.py
├── knowledge-base/
│   ├── 01-returns-policy-current.md
│   ├── 02-returns-policy-legacy.md
│   ├── 03-final-sale-and-promotions.md
│   ├── 04-damaged-or-wrong-items.md
│   ├── 05-domestic-shipping.md
│   ├── 06-international-shipping.md
│   ├── 07-warranty.md
│   ├── 08-order-changes-and-cancellations.md
│   ├── 09-trailplus-membership.md
│   ├── 10-gift-cards-and-price-adjustments.md
│   ├── 11-product-care.md
│   ├── 12-breeze-tumbler-product-card.md
│   ├── 13-support-escalation.md
│   └── 14-internal-content-migration-notes.md
├── data/
│   ├── orders.json
│   └── orders-data-dictionary.md
├── evaluation/
│   ├── visible-cases.json
│   └── custom-cases.json
├── storage/
│   └── faiss/          # generated by ingest.py, not committed
└── tests/
    ├── test_agent.py
    └── test_orders.py  # currently broken — see Bug Diary #1
```
 
