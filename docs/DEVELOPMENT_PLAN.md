# First development milestone: grounded business answers

The remaining work is an estimated 30–40 hours for the initial development
milestone, with estimates refined during implementation. This is a planning
estimate, not a delivery commitment or a limit on further development.
All R1–R7 packages below remain pending. The [roadmap](../ROADMAP.md) summarizes
priorities and dependencies; this file is the canonical engineering specification.
Its scope describes a first implementation, not a general document platform or a
reliability guarantee.

## R1 — Knowledge ingestion, retrieval, and answer integration

**Problem.** Sending all Avito FAQs in a static prompt spends context on unrelated
answers, lacks source references, and makes growing knowledge awkward. Existing
history can also mix contexts where account IDs are absent from its path.

**Change and locations.** Retain SQLAlchemy account configuration and existing
FAQ records. Adapt `database.Faq`, `repository.get_avito_accounts_faqs`, and
`utils.generate_gpt_prompt`; connect retrieval through
`message_handler.generate_chatgpt_answer`. Pass a trusted channel/account key
from `telegram_bot.py`, `avito_bot.py`, and `tc/messages.py`. Namespace account
types as well as numeric IDs so a Telegram account and an Avito account cannot
collide. Existing FAQ rows belong only to Avito accounts; do not invent a current
Telegram FAQ relationship. Proposed new modules: `knowledge/ingest.py`,
`knowledge/store.py`, and `knowledge/retrieve.py` (none exists yet).

### Ingestion contract

- Accept UTF-8 Markdown/TXT files and an adapter for existing account FAQ rows.
  Reject unsupported extensions and decoding errors without changing an index.
  No PDF/OCR, crawling, admin UI, or broad document-management abstraction.
- Proposed interface; not implemented:
  `python -m knowledge.ingest --channel avito --account-id 1 --source-id workshop --path examples/knowledge/synthetic_faq.md --reindex`.
  The CLI resolves `avito:1` against the configured database (`DATABASE_DNS`);
  it must reject unknown accounts. `--channel` selects the account table,
  `--account-id` its primary key, `--source-id` a stable operator-chosen source
  within that scope, and `--path` a local file. The alternative
  `--faq-records` reads the selected Avito account's FAQ rows, with stable row IDs
  as source IDs; it is mutually exclusive with file input. No credentials appear
  in CLI arguments. The CLI is a trusted operator action, never a message tool.
- Deterministic ordered chunking with validated configurable size and overlap
  (`0 <= overlap < size`). Record trusted account scope, document/source ID,
  chunk position, source heading/line range, content hash, and embedding identity.
  Derive stable chunk IDs from scope/source/position; repeated identical input
  has identical IDs. Do not expose absolute private document paths in answers.
- Use the external OpenAI embedding API behind R2's small adapter. Require an
  explicit operator-selected embedding model; record provider, model, vector
  dimension, distance metric, and chunking version in the index manifest. Do not
  silently use Chroma's default embedding function or download a local model.
  A model/dimension/chunking incompatibility stops ingestion/querying with an
  explicit reindex instruction; no mixing incompatible vectors.
- Use Chroma persistent local storage with explicit embeddings. First milestone
  operation is one application process owning an index directory, with serialized
  writes. Stop that reader while the separate ingestion CLI updates the directory;
  do not point the three Compose processes at one embedded database. Demonstrate
  one channel process at a time or separate per-process stores/reindex runs.
  Pin and verify the selected Chroma version's concurrency behavior; a hosted
  multi-process/server deployment is deferred.
- Reindexing is explicit. Prepare/validate chunks and embeddings first, upsert
  stable IDs, and remove only obsolete IDs in the same trusted account/source.
  Empty-source clearing must require the explicit reindex operation. A parse or
  embedding failure must not delete the last usable source. Embedded-store
  updates need not be advertised as atomic; stop readers during updates and leave
  a failure marker that requires a successful reindex before serving that source.
  Reindex the FAQ adapter's selected account set with a manifest so removed FAQ
  rows are cleaned up without touching other accounts or file sources.

### Retrieval and answer contract

- Embed the question with the recorded model. Apply the trusted account filter
  on every query and source lookup; reject missing scope. User text cannot choose
  scope, disable a filter, or supply an arbitrary collection. Test ingestion and
  deletion scoping as well. Filtering supports correctness; it is not a complete
  security boundary against a compromised process or database access.
- Bound query length, top-k, and the context budget. Select a distance metric,
  document its direction and range, and configure a relevance cutoff using the
  small synthetic cases. Do not equate distance with a confidence probability or
  invent a universal threshold. Skip unrelated chunks and cap total context,
  including the system prompt, current question, and retained conversation.
- Return a typed answer result with text, stable source IDs/location references,
  and status. Attach references from the selected chunks, not invented IDs from
  model text; retain result/source associations in persisted conversation data
  without breaking consumers expecting role/content messages. Only send supported
  message fields to the provider. Treat retrieved content as untrusted data,
  never as instructions to override policy or access another account.
- With no qualifying context, take a deterministic branch offering clarification
  or human follow-up. Do not call generation just to fabricate a sourced answer.
  Grounding instructions reduce unsupported answers but do not guarantee truth.
  Preserve phone/contact handling before retrieval, Telegram start/reset, existing
  prompts, and Avito non-text notification behavior.
- Add account scope to new Avito/client history paths and preserve Telegram bot
  scope. Do not auto-copy ambiguous old histories across accounts. Document that
  legacy files remain local and require explicit owner-directed mapping; new
  conversations start safely scoped. Full database/history migration is deferred.

**Dependencies.** R2 for real provider integration; R3 will reuse these functions.

**Acceptance.** With deterministic embedding/generation doubles and temporary
stores, ingest the [synthetic FAQ](../examples/knowledge/synthetic_faq.md), retrieve
the appointment-length source for a known question, exclude unrelated context for
a pricing question, and propagate the selected reference into the answer result.
Reopen the persistent index. Reindex identical input twice with unchanged IDs and
count; change/remove a section and verify old chunks disappear. Fail an embedding
call and verify the usable source is retained or blocked until recovery. Create
two accounts with the same local document ID and sender/chat identifiers; verify
retrieval, cleanup, and new conversation context never cross account boundaries.

## R2 — OpenAI compatibility and bounded failures

**Problem.** The pinned 0.28 SDK, legacy call/response access, blocking rate-limit
sleep, and partial error handling complicate both generation and new embeddings.

**Change and locations.** Update `requirements.txt`, `constants.py`, and
`message_handler.get_chat_completion`. Proposed `providers/openai_client.py`
holds small generation and embedding boundaries with normalized results/usage;
it is not a general provider framework. Use the official supported Python client
interface verified when implementation begins, preserving the existing message
contract. Choose and pin the SDK and supported model configuration then; no
migration deadline or API requirement can be inferred from the unsupplied notice.

Keep API keys in environment configuration and move generation/embedding model
selection into validated configuration. Define finite connect/read/request
timeouts, a total wall-time budget, and a small documented maximum attempt count.
Choose one retry owner: configure SDK retries explicitly and avoid wrapping them
in a second retry loop. Retry selected transient failures/rate limits within that
budget, honoring bounded server delay. Classify authentication and invalid-request
failures as non-retryable; return a controlled application fallback. A timeout can
leave completion unknown: retries cannot guarantee exactly-once execution or
absence of duplicate API charges. Credential rotation/account migration remains
separate from SDK work.

**Dependencies/boundaries.** Preserve shared contact/history behavior. Do not
rewrite Avito transport retries or add channel-send retries in this package.

**Acceptance.** Mock generation and embedding success, usage present/absent,
timeouts, rate limits, authentication failure, and invalid input. Verify attempt
count and total delay bounds using a fake clock, non-retryable failures make one
attempt, and existing reply/contact branches retain their behavior. Inspect logs
to ensure credentials and conversation content are absent from new error handling.

## R3 — Explicit LangGraph workflow

**Problem.** Retrieval, generation, missing evidence, and controlled failures need
distinct outcomes that can be tested without invoking a transport.

**Change and locations.** Proposed `conversation/workflow.py` defines a small
typed LangGraph state and conditional edges, invoked by `message_handler.py`.
State contains trusted account scope, current question, bounded conversation
context, retrieved chunks, source identifiers, and outcome/error classification.
Flow: retrieve → answer generation when relevant, otherwise no-context fallback;
controlled provider failure → error fallback; all paths return a result and end.
Make routing deterministic from state rather than asking a model to choose scope
or decide whether to retry. LangGraph makes these conditional transitions explicit
and independently testable as the product grows. No equivalent graph was found.

Reuse R1/R2 functions. Keep phone/email contact handling and channel sends outside
the graph; persist once at the existing application boundary with the minimum R1
history adjustments. No autonomous tools, agent teams, durable distributed
checkpoints, or transport rewrite.

**Dependencies.** R1/R2. **Acceptance.** Test relevant-context, no-context, and
controlled-error paths; assert returned text/status/sources, bounded node visits,
and one application send at most per handled input. Contact handling bypasses
retrieval/generation and sends its existing closing response once. These checks
do not promise end-to-end deduplication of repeated upstream channel events.

## R4 — Portable observability

**Problem.** Existing logs give no consistent counts, latency distributions,
retrieval/fallback frequency, or provider usage, and may include conversation text.

**Change and locations.** Proposed `observability/metrics.py` supplies shared
instruments around `message_handler.py`, R1 retrieval, R2 provider calls, and
channel application boundaries. Proposed `observability/collector.yaml` and an
opt-in Compose override will hold local infrastructure after implementation.
Neither configuration exists now. Use one application instrumentation path:

Python OpenTelemetry metrics SDK → OTLP → OpenTelemetry Collector Contrib.

The local Collector's Prometheus exporter exposes `/metrics` for an explicit
Prometheus scrape or manual inspection, optionally in OpenMetrics format. A
separate optional `awsemf` exporter converts metrics to CloudWatch Embedded Metric
Format and sends them to CloudWatch Logs, from which metrics are extracted.
Prometheus does not scrape an OTLP stream, and arbitrary application JSON does not
automatically become CloudWatch metrics.

### Proposed project metric contract

These application-specific names are a proposed project contract. Adopt verified
stable applicable semantic conventions at implementation time where appropriate;
do not claim that this naming scheme is an OpenTelemetry standard.

| Instrument | Type | Unit | Measurement and allowed attributes |
| --- | --- | --- | --- |
| `consultant.message.processed` | Counter | message | Once on completed application handling; `channel`, `outcome`. |
| `consultant.message.duration` | Histogram | s | Application input dispatch through reply/failure handling; `channel`, `outcome`; excludes waiting for a poll. |
| `consultant.retrieval.duration` | Histogram | s | Retrieval operation duration; `outcome`. |
| `consultant.retrieval.result_count` | Histogram | chunk | Selected context chunks, including zero; `outcome`. |
| `consultant.llm.request` | Counter | request | Each actual external attempt, generation or embedding; `operation`, `outcome`, configured `model`. |
| `consultant.llm.duration` | Histogram | s | External attempt latency; `operation`, `outcome`, configured `model`. |
| `consultant.llm.token.usage` | Counter | token | Provider-reported input/output tokens; `operation`, `token_type`, configured `model`. |
| `consultant.answer.fallback` | Counter | event | Once per fallback result; `channel`, `reason`. |

Define finite enums: channel `telegram_bot/avito/telegram_client`; operation
`generation/embedding`; outcome `success/no_context/timeout/rate_limit/auth_error/invalid_request/service_error/send_error`;
reason `no_context/provider_error`; token type `input/output`. Each instrument
accepts only its relevant subset. Count embeddings as input usage when that is
what the provider reports; omit unknown usage instead of fabricating zero or
monetary charges. Restrict `model` to the finite configured set, mapping unexpected
provider names to a fixed `other` value. Token counts are a cost proxy; money
requires a separately maintained pricing configuration, outside this milestone.

Never label metrics with phone numbers, account/chat/user IDs, paths, message
content, API keys, or arbitrary exceptions. Account scope is application state,
not a dimension. Set only bounded resource attributes such as service name and
environment; do not indiscriminately convert every resource attribute into labels.
Optional structured logs omit conversation content and secrets by default; remove
existing content-bearing debug/error fields on the exercised paths.

### Export behavior and version checks

At implementation, select a pinned Collector Contrib release and record its
version with the SDK/exporter versions. Validate both exporter configurations
using that binary. Deliver the local OTLP receiver + batch processor + Prometheus
exporter path first. Bind local exposition to loopback (or a private container
network) and document the scrape address, resource labels, and shutdown procedure.

Document the chosen Prometheus name translation (escaping/type/unit suffixes),
explicit histogram buckets, and cumulative/delta handling. For optional AWS,
document region, namespace, log group/stream, credentials through the AWS chain,
minimum required Logs permissions, metric declarations, and dimension allowlists.
Review dimension rollup defaults to avoid unintended extra series. Check EMF unit
mapping, cumulative-to-delta behavior, initial/reset counter handling, and how the
chosen release represents explicit/exponential histograms and summary data. If
conversion loses buckets, provide counts/sums or documented supported aggregates;
do not promise equivalent percentile queries between CloudWatch and Prometheus.

The AWS example must be version-checked and opt-in. AWS infrastructure provisioning
and live delivery tests are excluded unless separately authorized. Document its
status as configuration-validated, delivery-unverified when no AWS test occurs.
No exporter YAML or future environment keys are added during this preparation.

Use periodic batched export, finite export timeouts, bounded buffers, and graceful
shutdown/flush. Export failure must not fail a user response or create unbounded
blocking. Capture failures without recursive telemetry logging.

**Dependencies.** R2 boundary first, then R1/R3 hooks. **Acceptance.** Synthetic
requests produce expected counters, latency histograms, and usage in an in-memory
reader. Check finite attribute allowlists and absent sensitive attributes. Observe
the local Collector endpoint with synthetic traffic and verify naming/buckets.
Stop the Collector and verify normal responses continue within the documented
handling budget. Validate optional AWS configuration only; report delivery as
unverified until an actual authorized test supplies evidence.

## R5 — Offline integration and regression coverage

**Problem.** The repository has style checks but no behavior suite for shared
conversation handling or future cross-component changes.

**Change and locations.** Proposed `tests/` uses standard-library `unittest` and
`unittest.mock`, with temporary SQLite/Chroma directories and the synthetic FAQ.
Add a separate offline test job to `.github/workflows/code-quality.yml` after the
implementation; preserve flake8/Black. Prefer this small addition over introducing
a new test framework. Proposed interface; not implemented:
`python -m unittest discover -s tests -v`.

Cover account isolation in ingestion, retrieval, source lookup, deletion, and
conversation context; repeatable reindex/update/deletion and persistence; source
propagation; missing-context and controlled-error routing; SDK failure
classification/attempt budgets; telemetry counts/attribute restrictions; and the
shared processing flow with mocked Telegram/Avito/client sends and SMTP. Exercise
observable behavior, including reset/contact handling, rather than private method
sequences. Native TDLib imports must be replaceable so tests need not load its
bundled binaries.

Refactor import-time configuration/database initialization only as needed for
injected temporary configuration and adapters. Default tests use deterministic
embedding/LLM doubles, no live credentials, no outbound messages, and no downloaded
embedding model. Make unexpected runtime network attempts fail the tests. Package
installation may need network access; that is separate from test-runtime network
independence. Keep optional live smoke tests explicitly selected and outside the
default suite. No coverage percentage, training set, or model leaderboard is
promised.

**Dependencies.** Write tests with R1–R4; reserve this package for their combined
flow and regressions. **Acceptance.** Run the default suite on a clean environment
with service credentials unset, outbound connections blocked, and temporary
stores. Confirm no network attempts or generated data enter version control and
the existing formatting checks still run. No suite pass is claimed before it exists.

## R6 — Reproducible demo and handoff

**Problem.** New ingestion, workflow, and telemetry behavior needs one repeatable
demonstration without private databases or live conversations.

**Change and locations.** After implementation, update README and `.env.example`
with settings actually read by the new code. Document real ingestion/retrieval
commands, selected package/image versions, local index ownership, Collector
startup, and cleanup. Proposed `docs/DEMO.md` contains one end-to-end checklist:
create synthetic accounts/stores; ingest; ask a supported question; inspect sources;
ask an unsupported question; test isolation; update/reopen; inspect metrics; stop
the Collector; run regressions.

Provide an explicit offline mocked application-flow demo. It demonstrates routing,
history, sources, and instrumentation, not real language-model answer quality.
Real embedding/generation uses external API credentials; live Telegram/Avito and
SMTP need their own credentials and may send messages. The local Collector path
needs no AWS account. Optional AWS delivery stays unverified without an authorized
live test. Keep customer databases, conversation exports, indexes, and sessions
out of Git and image build contexts; inspect tracked artifacts separately.

**Dependencies.** R1–R5. **Acceptance.** Follow the documented checklist with fresh
temporary synthetic data; record actual checks, versions, and limitations. Verify
links and commands, default test network independence, and local exposition.
Completed documentation preparation is excluded from the remaining estimate.

## R7 — Basic CI/CD through Docker Hub and SSH

**Problem.** Compose currently builds locally, and CI only checks Python style
on pushes. There is no image-publication, server-deployment, or rollback workflow.
A public project benefits from an inspectable release path when registry/server
credentials remain separate from untrusted contributions.

**Scope and prerequisites.** One owner-provided Linux x86-64 server with Docker
Engine, Compose v2, persistent disk, and independently verified SSH access. The
owner supplies a host, Docker Hub repository, and credentials; no provider, price,
or existing server is assumed. Host purchase, OS setup/hardening from scratch,
infrastructure as code, and ongoing operations are outside this initial scope. If
prerequisites are absent, record the additional work and refine the estimate.
No resources or workflows are created during this documentation preparation.

Initially deploy one chosen Telegram bot or Avito process, one replica, and its
local Collector. Polling needs no public HTTP listener, domain, or reverse proxy.
Keep NocoDB and metrics private; use an SSH tunnel for administration. TDLib
clients, parallel pollers, and a shared multi-process Chroma store are deferred.

**Likely locations.** Adapt `Dockerfile`, `.dockerignore`, and
`.github/workflows/code-quality.yml`. Proposed files, not implemented:
`.github/workflows/publish-image.yml`, `.github/workflows/deploy.yml`,
`deploy/compose.yaml`, `deploy/deploy.sh`, and `docs/DEPLOYMENT.md`. The server
Compose file will reference an image digest without building on the server;
the existing Compose file remains the local-development entry point.

### CI and image publication

- PRs and main changes run lint/format, R5 offline tests, and an image build on
  GitHub-hosted runners. Fix the existing small style failures and reconcile tool
  versions; do not bypass gates. PR jobs have read-only repository permissions,
  no registry/deployment secrets, and no access to the server. Do not use the
  deployment host as a self-hosted runner for public PRs.
- Publish only the exact trusted main revision that passed those checks. Use a
  narrowly scoped Docker Hub token, minimum job permissions, and verified Docker
  actions pinned to full commit SHAs. Keep publication disabled until the owner
  enables it after contribution-rights and release-artifact review. A public
  repository does not require a public image; registry visibility is a separate
  choice, and private images do not eliminate contribution-rights obligations.
- Build a bot-only image with explicit COPY paths for required runtime modules
  and notices. Omit `tc/libs` and its unresolved binlog; user-account clients are
  outside this deployment slice. Exclude runtime credentials, databases, history,
  and indexes from layers, build arguments, caches, and logs. Inspect/scan the
  candidate artifact before publication. Pin the release dependency set and base
  image; record the source revision, full-commit tag, and returned digest.
- Tags can move: deploy and roll back using `repository@sha256:digest`, not
  `latest` or a tag alone. Build once and deploy that same checked artifact.

### SSH deployment, state, and rollback

- Start with manual dispatch from trusted main to a branch-restricted GitHub
  deployment environment; configure reviewer approval where available. Fork PRs
  never publish or deploy. Avoid privileged `pull_request_target` execution of
  PR code or untrusted artifacts. Validate a selected digest against a successful
  trusted publication record rather than accepting arbitrary shell input.
- Keep the SSH key in deployment-environment secrets. Independently verify the
  host key and enforce strict checking; unauthenticated `ssh-keyscan` alone does
  not establish identity. Use a dedicated deployment identity with rootless
  Docker where practical or a constrained server-side deployment wrapper.
  Docker-group membership is effectively root-level access, not isolation.
  A private image uses separate read-only pull credentials on the server.
- Runtime `.env` stays on the host with restricted permissions; CI need not read
  it. Mount SQLite, history, and the selected channel's index at stable paths.
  Demonstrate with synthetic data only. Serialize runs with GitHub concurrency
  and a host lock. Validate configuration, pull the digest, and run an offline
  preflight before stopping the old process; stop it fully before starting the
  new poller. Brief downtime is acceptable. Ingestion excludes active readers
  according to R1; no zero-downtime or exactly-once delivery claim is included.
- Record the previous digest/config version and make a consistent backup while
  the app is stopped before any state-changing upgrade. Check startup/process
  stability separately from application behavior: run R6's synthetic adapter
  scenario in an isolated smoke container with temporary stores and no outbound
  sends. A running container alone does not prove correct answers. Live channel
  or provider smoke requires separate explicit authorization.
- A failed startup/check leaves the release failed and restores the previous
  digest/config. If state is incompatible, require its matching backup or block
  the release; image rollback alone cannot undo data changes. Rehearse restore
  with synthetic data. No destructive migration or volume deletion in deployment.

**Scope boundary.** R7 covers host layout/Compose and state checks, extensions to
existing CI gates, bot-only image publication, SSH deployment and rollback,
synthetic acceptance checks, and a deployment runbook. Host provisioning and
provider costs are not included. R6 documents the application demo; R7 documents
its deployment. Existing style-check CI and Docker configuration are not counted
as future implementation work.

**Dependencies.** R5 checks, R6 smoke interface, R1 single-process index rules,
prepared host/registry, and confirmed publication rights. Owner-supplied host,
registry visibility, and secret values remain implementation-time inputs.

**Acceptance.** Show that a fork PR runs without secrets/publication; failing
checks block release; and a checked main revision maps to the digest deployed by
manual SSH execution. Confirm one poller, state preserved after restart/replacement,
no public admin/metrics port bindings, rejected unknown host keys, and rollback
from a bad image/startup. Exercise backup/restore and inspect image/logs for
credentials. Mock SSH/registry in default offline tests. An authorized real
registry/server trial is required before declaring remote deployment verified;
live channel verification remains separate. No such trial is claimed today.

## Proposed configuration, not current environment settings

Implementation will introduce validated generation/embedding model selection,
index path and identity, chunk size/overlap, retrieval top-k/distance cutoff,
context budget, request timeout/retry budget, and OpenTelemetry OTLP endpoint,
export interval/timeout, service name, and environment. Exact names/defaults will
be chosen and documented with the code. Current `.env.example` deliberately
contains only variables already read by `constants.py`. Never put API keys,
account scopes chosen by users, or AWS credentials in committed demo files.
