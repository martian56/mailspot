# Overview

The vocabulary, result model, and boundaries the other specs build on.

## What it does

Given an email address, say how usable it is. Given a name and a company
domain, work out the address and say the same. Always a score and a suggested
action, never a bare boolean. The honest answer is usually "probably," not
"yes."

## In scope for v1

- Syntax validation, normalization, and a provider-aware canonical form.
- MX resolution, mail-provider fingerprinting, and null-MX handling.
- SMTP mailbox probing (`RCPT TO`), best-effort, with graceful fallback.
- Provider-aware verification: branch the strategy on the mail provider, and
  never report a bare acceptance from a known-unverifiable provider as valid.
- Catch-all (accept-all) domain detection.
- Greylisting handling: retry temporaries, and a deferred outcome for bulk.
- Address classification: disposable, role-based, free-provider.
- Typo suggestion ("did you mean gmail.com?").
- A confidence score and a recommended decision, calibrated against false positives.
- An email finder: pattern detection from known samples, plus permutation.
- Bulk processing with bounded concurrency, CSV input/output, and a deferred
  re-check pass.
- Caching, per-domain rate limiting, adaptive per-host backoff, timeouts, retries.
- Proxy routing (SOCKS/HTTP) for SMTP, so it works from cloud hosts and spreads
  load across egress addresses.
- Observability hooks for metrics and logging.
- A provider interface for future external data sources (no integrations shipped).
- A command-line interface over the whole library.
- A maintenance script to refresh the classification lists.

## Out of scope for v1

- Shipping or bundling any contact dataset.
- Scraping the web to discover addresses (lives behind the provider interface,
  implemented by the operator, not by the core).
- Sending email of any kind. `mailspot` never delivers a message.
- Paid-provider integrations (Hunter, People Data Labs, etc.).
- SPF/DMARC domain-health scoring (the result model leaves room for it later).

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
- **Provider strategy**: how verification is handled for a given mail provider.
  Some providers answer honestly; some accept everything and decide later.
- **Canonical form**: the address reduced to the mailbox it really targets, using
  provider rules (Gmail ignores dots and anything after `+`), used for dedup.
- **Greylisting**: a server temporarily refusing (a 4xx) to slow down senders,
  not a rejection.
- **Deferred**: an address whose answer was a temporary refusal, to be re-checked
  later rather than called invalid.

## The result model

Two result types. Both are typed, serializable to JSON, and carry the evidence
behind the headline, not just the headline.

### VerificationResult

| Field | Meaning |
|---|---|
| `email` | The normalized address that was checked. |
| `canonical` | The provider-canonical mailbox (dots/`+` resolved), for dedup. |
| `status` | `valid` \| `invalid` \| `risky` \| `unknown` (see below). |
| `decision` | `send` \| `verify_first` \| `skip` \| `unknown`: what to do next. |
| `confidence` | Integer 0-100. |
| `provider` | The fingerprinted mail provider, or `null`. |
| `deferred` | True when the answer was a temporary refusal and a re-check is advised. |
| `suggestion` | A likely typo correction (`jane@gmial.com` -> `jane@gmail.com`), or `null`. |
| `checks.syntax` | `{ valid, normalized, canonical, reason }`. |
| `checks.mx` | `{ found, hosts, provider, null_mx }`. |
| `checks.smtp` | `{ attempted, deliverable, code, reason, skipped_reason, transcript }`. |
| `checks.catch_all` | `{ tested, is_catch_all }`. |
| `flags` | `{ disposable, role, free_provider }`. |
| `reason` | One human-readable sentence summarizing the outcome. |

`transcript` is a short, ordered list of the SMTP exchange (command and response
code), for auditing why a result came out the way it did. It never contains
message content, because none is sent.

### FinderResult

| Field | Meaning |
|---|---|
| `name` / `domain` | The query. |
| `best` | The highest-confidence candidate, or `null` if none is credible. |
| `candidates` | All generated candidates, each with its `VerificationResult`. |
| `detected_pattern` | The pattern inferred from samples, or `null`. |
| `method` | `pattern_detected` \| `permutation`. |

### Status definitions

- **valid**: strong evidence the mailbox exists and accepts mail (a trustworthy
  acceptance on a domain that is not catch-all and not known-unverifiable).
- **invalid**: strong evidence it does not (bad syntax, no MX, null MX, hard SMTP
  reject).
- **risky**: plausible but unproven: catch-all domain, role address, a
  known-unverifiable provider, or an SMTP answer that was not definitive.
- **unknown**: not enough evidence either way (checks were blocked or skipped).

A known-unverifiable provider (Gmail, Outlook, Yahoo and the like, which accept
every probe) never yields `valid` from SMTP alone. That is the main guard against
false positives, and it is why provider-aware handling matters.

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
mailspot.verify(email, *, options=...) -> VerificationResult          # async
mailspot.find(name, domain, *, samples=..., options=...) -> FinderResult   # async
mailspot.verify_many(emails, *, options=...) -> list[VerificationResult]   # async
mailspot.recheck(results, *, options=...) -> list[VerificationResult]  # re-run deferred
mailspot.suggest(email) -> str | None                                 # typo correction, sync
mailspot.canonical(email) -> str                                      # canonical form, sync
mailspot.sync.verify(...) / find(...) / verify_many(...) / recheck(...)   # sync wrappers
```

`suggest` and `canonical` are pure and offline, so they stay synchronous. The
CLI (`cli.spec.md`) is a thin front end over exactly these.

A capability is done when its feature file passes.
