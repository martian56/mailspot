# Overview

The vocabulary, result model, and boundaries the other specs build on.

## What it does

Given an email address, say how usable it is. Given a name and a company
domain, work out the address and say the same. Always a score and a suggested
action, never a bare boolean. The honest answer is usually "probably," not
"yes."

## In scope for v1

- Syntax validation and normalization.
- MX resolution and mail-provider fingerprinting.
- SMTP mailbox probing (`RCPT TO`), best-effort, with graceful fallback.
- Catch-all (accept-all) domain detection.
- Address classification: disposable, role-based, free-provider.
- A confidence score and a recommended decision.
- An email finder: pattern detection from known samples, plus permutation.
- Bulk processing with bounded concurrency and CSV input/output.
- Caching, per-domain rate limiting, timeouts, and retries.
- A provider interface for future external data sources (no integrations shipped).
- A command-line interface over the whole library.

## Out of scope for v1

- Shipping or bundling any contact dataset.
- Scraping the web to discover addresses (lives behind the provider interface,
  implemented by the operator, not by the core).
- Sending email of any kind. `mailspot` never delivers a message.
- Paid-provider integrations (Hunter, People Data Labs, etc.).

## Vocabulary

- **Address**: a full email like `jane.doe@acme.com`.
- **Local part**: the text before the `@` (`jane.doe`).
- **Domain**: the text after the `@` (`acme.com`).
- **MX record**: the DNS record naming the server that accepts mail for a domain.
- **Catch-all / accept-all**: a domain whose server accepts every address,
  so a successful SMTP probe proves nothing about a specific mailbox.
- **Role address**: a shared, non-personal mailbox: `info@`, `sales@`, `support@`.
- **Disposable**: a throwaway/temporary-mail domain.
- **Free provider**: a consumer mailbox domain: `gmail.com`, `outlook.com`.
- **Pattern**: a company's local-part convention, e.g. `{first}.{last}`.
- **Probe**: an SMTP conversation that asks whether a mailbox exists without
  sending a message.

## The result model

Two result types. Both are typed, serializable to JSON, and carry the evidence
behind the headline, not just the headline.

### VerificationResult

| Field | Meaning |
|---|---|
| `email` | The normalized address that was checked. |
| `status` | `valid` \| `invalid` \| `risky` \| `unknown` (see below). |
| `decision` | `send` \| `verify_first` \| `skip` \| `unknown`: what to do next. |
| `confidence` | Integer 0-100. |
| `checks.syntax` | `{ valid, normalized, reason }`. |
| `checks.mx` | `{ found, hosts, provider }`. |
| `checks.smtp` | `{ attempted, deliverable, code, reason, skipped_reason }`. |
| `checks.catch_all` | `{ tested, is_catch_all }`. |
| `flags` | `{ disposable, role, free_provider }`. |
| `reason` | One human-readable sentence summarizing the outcome. |

### FinderResult

| Field | Meaning |
|---|---|
| `name` / `domain` | The query. |
| `best` | The highest-confidence candidate, or `null` if none is credible. |
| `candidates` | All generated candidates, each with its `VerificationResult`. |
| `detected_pattern` | The pattern inferred from samples, or `null`. |
| `method` | `pattern_detected` \| `permutation`. |

### Status definitions

- **valid**: strong evidence the mailbox exists and accepts mail.
- **invalid**: strong evidence it does not (bad syntax, no MX, hard SMTP reject).
- **risky**: plausible but unproven: catch-all domain, role address, or SMTP
  that could not give a definitive answer.
- **unknown**: not enough evidence either way (checks were blocked or skipped).

`status` is the honest classification; `decision` is the recommended action
derived from it. They are specified fully in `confidence-and-decision.spec.md`.

## Design principles

1. **Return evidence, not verdicts.** Every headline carries the checks that
   produced it, so a caller can apply their own policy.
2. **Honest degradation.** When a check cannot run (port blocked, provider
   refuses, timeout), the result records *why* and the score reflects the
   missing evidence. The library never fabricates certainty.
3. **Async-first, sync-friendly.** The core is `asyncio`; a thin synchronous
   wrapper exists so a casual caller is not forced into an event loop.
4. **Polite by default.** Bounded concurrency, per-domain rate limiting, DNS
   and connection caching, and timeouts are on out of the box.
5. **No hidden network beyond what the job needs.** DNS and SMTP only, to the
   domains the caller named. No telemetry, no bundled data, no third-party calls.
6. **One clear job per component.** Each check is independent and testable in
   isolation; the pipeline composes them.

## Public surface (shape, not implementation)

```
mailspot.verify(email, *, options=...) -> VerificationResult        # async
mailspot.find(name, domain, *, samples=..., options=...) -> FinderResult  # async
mailspot.verify_many(emails, *, options=...) -> list[VerificationResult]  # async
mailspot.sync.verify(...) / find(...) / verify_many(...)            # sync wrappers
```

The CLI (`cli.spec.md`) is a thin front end over exactly these.

A capability is done when its feature file passes.
