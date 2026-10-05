# Architecture

How it's put together, and why it's shaped for bulk rather than one-off lookups.

## Layering

Four layers, each depending only on the one below it.

```
  CLI  (typer)                     thin front end, no logic of its own
   │
  Orchestration                    verify(), find(), verify_many(): compose checks,
   │                               apply concurrency, assemble results
   │
  Checks                           syntax · mx · smtp · catch_all · classification
   │                               each independent, each returns a sub-result
   │
  Infrastructure                   DNS client, SMTP client, cache, rate limiter,
                                   clock/timeouts, provider interface
```

The dependency rule is strict: a check never calls another check, and nothing
below orchestration knows what a "decision" is. Scoring and decision live in
orchestration, over the raw check outputs.

## Module map

```
src/mailspot/
  __init__.py          public async API: verify, find, verify_many, result types
  models.py            VerificationResult, FinderResult, enums, check sub-results
  options.py           Options: timeouts, concurrency, toggles, from-mail identity
  errors.py            the library's exception hierarchy

  checks/
    syntax.py          parse + normalize + validate the address
    mx.py              resolve MX, order by preference, fingerprint provider
    smtp.py            RCPT TO probe, connection handling, result mapping
    catch_all.py       probe a random local part to detect accept-all
    classify.py        disposable / role / free-provider flags

  scoring.py           check outputs -> status -> confidence -> decision
  finder.py            pattern detection + permutation + candidate ranking
  patterns.py          the pattern catalogue and {first}{last}... expansion

  infra/
    dns.py             async DNS with caching
    smtp_client.py     async SMTP sessions, per-host reuse
    cache.py           TTL cache (MX, catch-all verdicts)
    ratelimit.py       per-domain limiter
    providers.py       Provider protocol + resolver chain (no integrations)

  data/
    disposable.txt     known disposable domains (static list, updatable)
    free.txt           known free-provider domains
    roles.txt          known role local-parts

  sync.py              synchronous wrappers over the async API
  cli.py               typer app
```

## Data flow: a single verify

1. **Syntax** parses and normalizes the address. A hard failure ends the run
   immediately with `status=invalid`; nothing downstream is attempted.
2. **Classification** flags disposable / role / free-provider from the static
   lists. Cheap, local, no network.
3. **MX** resolves the domain. No MX means mail cannot be delivered →
   `status=invalid`. The result caches per domain.
4. **Catch-all** probes a random, almost-certainly-nonexistent local part. If
   the server accepts it, the domain is accept-all and any later per-mailbox
   success is not trustworthy. Verdict caches per domain.
5. **SMTP** probes the real local part, unless the domain is catch-all (then it
   is pointless) or SMTP is disabled/unavailable (then it is skipped with a
   reason).
6. **Scoring** turns the collected evidence into `status`, `confidence`, and
   `decision`.

Steps that do not depend on each other may run concurrently; MX must precede
catch-all and SMTP because both need the mail host.

## Async model

The core is `asyncio`. Rationale: the work is almost entirely I/O wait (DNS,
TCP, SMTP round-trips), so concurrency, not parallelism, is what makes bulk
fast. `verify_many` runs addresses concurrently under a global semaphore and a
per-domain rate limiter, and groups addresses by domain so MX and catch-all
verdicts are resolved once per domain and reused.

`sync.py` wraps each coroutine with `asyncio.run` for callers who do not want an
event loop. The sync layer adds no behaviour; it only bridges.

## Scale decisions (deliberate, from day one)

- **Resolve-once-per-domain.** MX records and catch-all verdicts are cached with
  a TTL, so a bulk run over 10,000 addresses at 400 domains does ~400 MX
  lookups, not 10,000.
- **Group bulk by domain.** Addresses at the same domain share one SMTP session
  where the server allows it, and respect one rate limiter.
- **Bounded everything.** A global concurrency cap, a per-domain rate limit, and
  timeouts on every network call keep the tool from overwhelming a server or
  itself.
- **Streaming bulk.** Bulk input is processed as a stream and results are
  yielded as they complete, so memory does not grow with input size and a long
  run produces output continuously.
- **Pure checks.** Each check is a pure function of its inputs plus its injected
  infrastructure client, so each is unit-testable without network and the
  pipeline is deterministic under test via fakes.

## Provider interface (seam only, no integrations in v1)

External data sources (paid enrichment APIs, or an operator's own scraper)
implement a single `Provider` protocol and register in a resolver chain. The
finder consults the chain for known `(name, email)` samples before falling back
to permutation. v1 ships the protocol and an empty default chain; it ships no
providers. This keeps the core free of any contact data and lets the operator,
not the library, decide what sources to use.

## Dependencies (curated, minimal)

| Dependency | Why | Rejected alternative |
|---|---|---|
| `dnspython` (+ async resolver) | MX resolution with async support | hand-rolled DNS |
| `aiosmtplib` | async SMTP sessions | blocking `smtplib` in threads |
| `pydantic` v2 | typed, validated, JSON-serializable results | hand-written `to_dict` |
| `typer` | declarative CLI with help/validation | raw `argparse` boilerplate |

Standard library covers the rest. No dependency is added without a line here
justifying it.

## Errors

A small hierarchy under `MailspotError`: `ConfigurationError` (bad options),
`DomainResolutionError` wrapped internally into a check result rather than
raised to the caller. The public API does not raise on an un-verifiable
address: an un-verifiable address is a *result* (`unknown`), not an exception.
Exceptions are reserved for misuse and programmer error.

## Testing strategy

- **Unit**: each check against fakes (fake DNS, fake SMTP), no network. The
  bulk of the suite.
- **BDD** (`features/`): behaviour of the public API and CLI, via pytest-bdd,
  against injected fakes so scenarios are deterministic and offline.
- **Integration**: a small, opt-in, network-gated set against real domains,
  skipped by default in CI, for sanity only.

No test in the default suite touches the network.
