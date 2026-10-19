# Initial development milestone

The remaining work is an estimated 30–40 hours for the initial development
milestone, with estimates refined during implementation. This is a planning
estimate, not a delivery commitment or a limit on further development.
Retrieval-augmented generation (RAG) is the main product improvement.

## Remaining priorities and completion checks

The inspected code still uses static Avito FAQ prompting, legacy OpenAI calls,
and file-based history, with no ChromaDB, LangGraph, or OpenTelemetry integration.
Related unpublished work must be reconciled before implementation so completed
scope is not counted again. R7 assumes one owner-provided Linux server with
Docker Engine, Compose, and verified SSH access already available.

| ID | Work package | Dependencies | Status | Observable acceptance criteria |
| --- | --- | --- | --- | --- |
| R1 | Knowledge ingestion, ChromaDB retrieval, and answer integration | R2 before embedding/generation integration | [ ] Pending | Synthetic sources survive reopen; relevant sources reach answers; unsupported questions fall back; reindex removes stale chunks; retrieval and history stay within the trusted account. |
| R2 | OpenAI SDK compatibility and bounded failure handling | Existing message-handler behavior | [ ] Pending | Mock generation/embedding success and classified failures; finite timeout/retry budget; existing contact and reply behavior preserved. |
| R3 | Explicit conversation workflow with LangGraph | R1, R2 | [ ] Pending | Relevant, missing-context, and controlled-failure paths route deterministically; graph execution does not repeat channel sends. |
| R4 | OpenTelemetry metrics and Collector export paths | R2 boundaries; R1/R3 hooks as available | [ ] Pending | In-memory counts and attributes pass; local Collector exposes metrics; export outage leaves message processing functional; optional AWS config is version-checked. |
| R5 | Offline integration and regression tests | Checks alongside R1–R4; final integration after R3/R4 | [ ] Pending | Temporary stores and deterministic provider/channel doubles cover isolation, reindex, sources, fallback, retry bounds, and metrics without runtime network access. |
| R6 | Reproducible demo, setup documentation, and final verification | R1–R5 | [ ] Pending | A fresh local synthetic demo and documented checklist distinguish mocked behavior, credentialed API calls, and unverified AWS delivery. |
| R7 | Basic CI/CD: Docker Hub image and SSH deployment to one server | R5 checks; R6 demo; prepared server and registry; publication rights resolved | [ ] Pending | PRs have no deployment secrets; checked main revision produces an image; manual deployment pins its digest; synthetic smoke and rollback preserve data; no duplicate poller is started. |

Detailed scope, proposed interfaces,
metric definitions, checks, and deferred work live only in the
[canonical engineering plan](docs/DEVELOPMENT_PLAN.md).
