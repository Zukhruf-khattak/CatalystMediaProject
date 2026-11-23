# 08 — Security and Privacy Policy

## 1. Secrets Management
- All sensitive variables (database passwords, API tokens, endpoints) are managed exclusively through environment variables.
- `.env` is explicitly ignored by version control (`.gitignore`).
- `.env.example` contains only harmless placeholders and documentation.
- The health endpoint (`/api/v1/health`) strictly exposes high-level metadata (status, version, app name) and never prints connection strings, database credentials, or secret keys.

---

## 2. CORS (Cross-Origin Resource Sharing)
- Cross-Origin Resource Sharing is controlled via `ALLOWED_ORIGINS` in `Settings`.
- Wildcard `*` origins are strictly prohibited in production configurations.
- Default local configuration permits only trusted local development hosts (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`).

---

## 3. Telemetry and Logging Redaction
- **No Raw Transcript Leaks to Traces**: External tracing (LangSmith) receives only operational metadata, node latencies, and tool parameter shapes. Raw meeting transcript text is redacted or kept local to prevent unintentional PII exfiltration.
- **Structured Log Safety**: Application logs output JSON with timestamp, severity, logger name, and request ID. Database credentials and authentication tokens are masked.

---

## 4. Local-Only Execution Mode
- The system is architected to operate 100% offline using local Ollama LLMs and local `sentence-transformers` CPU embeddings.
- No network call is made to third-party proprietary APIs unless the user explicitly configures an optional Gemini key.

