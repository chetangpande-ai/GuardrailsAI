# Guardrails Lab

A local-first Python CLI for revising practical AI guardrails. The deterministic
demos and tests work without network access or an API key. An optional Groq
command lets you experiment with a real model after you add your own key.

## Setup with uv

Install [uv](https://docs.astral.sh/uv/), then run these commands from this
directory:

```powershell
uv sync --extra dev
uv run guardrails-lab
uv run pytest
```

The project supports Python 3.10 and newer. `uv` creates and manages the local
`.venv` and lockfile.

## What the demos teach

- **Output schema:** Pydantic checks field types, allowed values, lengths, and
  unexpected fields. Valid JSON is not necessarily valid schema output.
- **Privacy:** a small regex baseline redacts complete email and Indian mobile
  matches. It is not comprehensive PII detection.
- **Prompt injection:** a keyword detector is shown as a fallible signal, not a
  security boundary. It can miss paraphrases and flag harmless quotes.
- **RAG access:** tenant and team permissions filter documents before their
  content is included in context. Retrieved text remains untrusted.
- **Tool authorization:** server-side roles, beneficiary allowlists, approval,
  and idempotency protect a simulated transfer. No real payment is made.
- **Evaluation:** a small labeled set demonstrates precision, recall, and
  false-positive rate; it is not a security certification.
- **Pipeline:** an end-to-end mock response is schema-checked and redacted.

Try `uv run guardrails-lab --help` for commands. The default `demo` command runs
all offline examples.

## Optional Groq experiment

1. Copy `.env.example` to `.env`.
2. Add your Groq API key to `GROQ_API_KEY` in `.env`.
3. Install the optional client and run an explicit live request:

```powershell
uv sync --extra dev --extra groq
uv run guardrails-lab ask "Review the movie Inception"
```

The `ask` command sends the prompt to Groq only when you explicitly run it.
Never commit `.env` or paste a real secret into source code or notebooks. The
live example is for learning; it does not make the keyword detector or
application a production security boundary.

## Project map

```text
src/guardrails_lab/
  guardrails/
    checks.py     PII redaction and injection signal
    pipeline.py   Mock and optional Groq response pipeline
    schemas.py    Strict Pydantic output schema
  retrieval/
    access.py     RAG document authorization
  tools/
    authorization.py  Server-side simulated transfer policy
  evaluation/
    metrics.py   Small detector evaluation metrics
  cli.py          CLI and offline demonstrations
tests/
  unit/
    test_guardrails.py
```

## Security boundaries to remember

- Authorization belongs in the trusted backend, not in model instructions or
  model-generated claims about a user's role.
- Filter document access before retrieval and before building model context.
- Validate the final output for its destination; schema validity does not prove
  facts are true or content is safe.
- Treat detectors as imperfect, evaluate false positives and false negatives,
  and require independent approval for consequential actions.
- The transfer approval flag and ledger are in-memory teaching examples, not
  authenticated, atomic, or durable transaction processing.

## System design principles

This project is a small example of a security-sensitive application, not just
a collection of AI filters. Its flow is:

```text
CLI
 ├── deterministic guardrail demonstrations
 ├── retrieval access checks
 ├── simulated tool authorization
 └── optional Groq request
       └── validate response -> redact PII -> return result
```

The package separates guardrails, retrieval, tool authorization, and evaluation
so that each responsibility can be understood and tested independently. The
pipeline accepts a generator function, allowing deterministic tests to exercise
guardrail behavior without a network call, API key, or live model.

Principles demonstrated:

- **Defense in depth:** input signals, schema validation, PII redaction, data
  access checks, and tool authorization are separate layers. A detector passing
  does not replace authorization at the point of action.
- **Least privilege:** server-side roles and beneficiary allowlists determine
  whether a simulated tool action is permitted; model-generated claims cannot
  grant permissions.
- **Authorization before data exposure:** filter documents before their content
  is added to model context. Retrieved documents remain untrusted data.
- **Explicit contracts:** Pydantic schemas define accepted output fields,
  values, and constraints instead of assuming model output is well formed.
- **Configuration and secret hygiene:** keep credentials out of source control;
  use environment-specific configuration such as `.env`, which is ignored by
  Git.
- **Testable behavior:** automate checks for both valid and invalid inputs,
  permission boundaries, redaction, and failure actions.

## Future enhancements

The current demos are intentionally local and simplified. If extending this
project beyond a learning CLI, consider the following in roughly this order:

1. **Threat model and trust boundaries**
   - Identify assets and failure modes first: private data, cross-tenant
     exposure, prompt injection, unsafe tool use, misinformation, and cost
     abuse.
   - Treat user input, retrieved documents, tool output, and model-generated
     arguments as untrusted.
   - Make authorization decisions in trusted backend code, not in prompts or
     classifier scores.

2. **Real identity and authorization**
   - Replace hard-coded users and permissions with authenticated identities and
     a well-defined server-side policy.
   - Enforce tenant and document permissions in the retrieval layer and check
     access again when loading protected content.
   - Keep permissions specific to each tool; read-only search and a
     side-effecting operation should not share a generic authorization rule.

3. **Safe tool execution**
   - Replace the in-memory dictionary with durable storage and make the
     idempotency check and write atomic across processes and restarts.
   - Replace the demo approval Boolean with an authenticated, auditable
     approval tied to the exact action and parameters, with appropriate expiry.
   - Add parameter limits, allowlisted destinations, rate limits, timeouts,
     bounded retries, and cost budgets.
   - Fail closed for privileged or irreversible operations if authorization or
     approval cannot be verified.

4. **Stronger privacy and output controls**
   - Treat the regex PII detector as a teaching baseline; evaluate a suitable
     recognizer such as Presidio for the application's languages and data.
   - Minimize sensitive data retrieval and retention, redact whole entities,
     and avoid logging secrets or unnecessary raw prompts and responses.
   - Validate output for its destination. Schema validity does not prove that
     claims are true, safe, or correctly grounded in authorized evidence.

5. **Evaluation and operations**
   - Expand labeled tests to cover benign quoted text, direct and indirect
     attacks, paraphrases, multilingual content, obfuscation, and edge cases.
   - Track false-positive and false-negative rates, precision, recall, PII leak
     rate, unauthorized actions, task completion, latency, and cost.
   - Combine offline regression tests with privacy-aware production monitoring,
     versioned policies, incident response, and rollback procedures.

6. **Optional application interface**
   - If adding an API or UI, keep the same guardrail and authorization
     boundaries in the service layer; do not make a client-side check the
     security boundary.
   - Add integration tests for request handling, authentication, authorization,
     provider failures, and output validation.

These are enhancement directions, not guarantees of production readiness. The
current in-memory ledger, demo identities, small synthetic evaluation set, and
keyword-based injection detector are instructional examples only.
