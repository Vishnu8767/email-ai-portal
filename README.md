# 📥 Global Email Intelligence Portal

An enterprise-grade, multi-stage automation pipeline that securely intercepts incoming emails, applies advanced text sanitization and Optical Character Recognition (OCR), processes content through an optimized chain of **NVIDIA Llama 3.3 70B** models, and auto-dispatches highly authentic, tone-preserved human replies back to the sender.

---

## 🚀 System Architecture & Core Workflow

The application operates as a fully closed-loop automation cycle across three major architectural layers:
### 1. Inbound Ingestion Layer (IMAP Core)
* **Target Handshake:** Connects to Gmail over an encrypted `IMAP4_SSL` wrapper.
* **Header & Metadata Isolation:** Dynamically reads and caches the last 10 email threads, mapping out sender identity parameters (`From`), tracking lines (`Subject`), and message bodies (`Body`).
* **HTML Entity Sanitization:** A multi-pass regular expression engine strips out script markers, cascading stylesheets (CSS), and layout markup. It handles hidden layout tricks used by spam systems by decoding HTML fragments (e.g., `&#8199;`, `&shy;`) using Python's `html.unescape()` core.

### 2. Optical Character Recognition (OCR Engine)
* **Graphical Asset Interception:** When multi-part MIME layers discover embedded image payloads or inline screenshots, the system isolates the raw binary buffers.
* **Tesseract Engine Parsing:** Images are routed into `pytesseract`. Text embedded within image matrices is extracted cleanly and appended to the primary textual document payload before any AI processing begins.

### 3. Multi-Stage Cognitive Layer (NVIDIA NIM Model Chain)
Instead of running a single generic prompt, the system breaks processing down into isolated cognitive phases running on **Meta Llama 3.3 70B Instruct**:

* **Phase A (Phonetic Language Fingerprinting):** Scans regular text scripts and Romanized/Transliterated content (e.g., regional language terms spelled using the English alphabet like *"emi chestunav"* or *"kya kar rahe ho"*). It filters out proper nouns and academic acronyms to identify the underlying regional tongue natively.
* **Phase B (Deterministic Translation):** Normalizes mixed-language payloads cleanly into fluent English. The processing temperature is locked at `0.0` to preserve transaction values, balance metrics, dates, and account details.
* **Phase C (Word-by-Word Tone Profiler):** Analyzes the contextual purpose of the communication across every sentence. If routine life checks or casual phrases are present beneath formal headers, it categorizes the interaction register as **Friendly** instead of formal.
* **Phase D (Character Persona Drafting & Fallback Core):** Generates responses anchored to a specialized personal profile engine (tracking student identity, technical algorithmic frameworks like NLP, routine schedules, and specific interests). If the message covers unmapped topics, a dynamic fallback routine deploys simulated human intuition to draft realistic responses, while strict anti-bot overrides remove boilerplate phrases like *"As an AI..."*.
* **Phase E (Structural Reverse Translation):** Translates the English response back into the sender's language, explicitly supplying missing implicit verbs to ensure complete, natural sentence fragments rather than raw, fragmented word substitutions.

### 4. Outbound Automated Dispatch Layer (SMTP Core)
* **Threading Integrity:** Evaluates the initial tracked topic and appends standard `Re:` notation to stitch the outgoing text smoothly into the client's current email client sequence.
* **Secure Delivery:** Spins up an autonomous network handshake (`smtplib`) using secure port 465 SSL protocols to log in and instantly dispatch the response back to the sender's origin.

---

## 🛡️ Smart Pacing Engine (HTTP 429 Rate-Limit Recovery)

To handle rapid bursts of sequential API execution, the client code implements a robust network interceptor configured with an **Exponential Backoff Retry Strategy**:

| Attempt Cycle | Trigger Condition | Backoff Delay Strategy | Behavior |
| :--- | :--- | :--- | :--- |
| **First Intercept** | Server Status `429` | Wait **2 Seconds** | Pause pipeline execution, clear sockets, and attempt retry. |
| **Second Intercept** | Server Status `429` | Wait **4 Seconds** | Double backoff window to allow remote server queue mitigation. |
| **Third Intercept** | Server Status `429` | Wait **8 Seconds** | Escalate backoff delay automatically. |
| **Max Cap Failure** | Persistent `429` | Halt Processing | Safe shutdown execution via automated code circuit breaker. |

---

## 🛠️ Tech Stack & Dependencies

* **Language Workspace:** Python 3.10+
* **User Interface Framework:** Streamlit (Core reactive web server dashboard topology)
* **Linguistic Cognitive Core:** NVIDIA NIM Inference API (`meta/llama-3.3-70b-instruct`)
* **Computer Vision Core:** Google Tesseract OCR System + `pytesseract`
* **Secure Mail Protocols:** `imaplib` (Encrypted message ingestion), `smtplib` (Secure SSL outbound transmission)

---

## 📂 Repository Layout

```text
├── app.py               # Principal Streamlit application code and cognitive pipelines
├── requirements.txt     # Python package management mapping file
└── packages.txt         # System-level Linux application dependencies (Tesseract Core)
