# Infrastructure: Caching, Rate Limiting, Timeouts, Providers

The shared machinery under the checks. None of it is user-facing on its own, but
all of it is configurable through `Options`, and it is what makes the library
safe to point at real servers and fast in bulk.

## Options

A single `Options` object carries every knob, with sensible defaults, passed
into any public call. Fields:

- `smtp_enabled` (default true)
- `catch_all_enabled` (default true)
- `concurrency`: global in-flight cap (default sensible-for-a-laptop)
- `per_domain_rate`: max probes/second to one domain
- `dns_timeout`, `smtp_timeout`, `connect_timeout`
- `smtp_retries`: retries on a 4xx/transient (default 1)
- `mx_cache_ttl`, `catch_all_cache_ttl`
- `probe_identity`: the `EHLO` host and `MAIL FROM` address
- `extra_disposable`, `extra_free`, `extra_roles`: list extensions/overrides
- `providers`: the resolver chain (empty by default)

Invalid options raise `ConfigurationError` at the call boundary, not deep inside.

## Caching

- A TTL cache keyed by domain holds MX results and catch-all verdicts.
- Cache is in-process and bounded; entries expire by TTL.
- The cache is injected, so tests use a controllable fake and nothing is global
  or hidden.

## Rate limiting

- A per-domain limiter enforces `per_domain_rate` so one server is never hit
  faster than configured, independent of global concurrency.
- The global semaphore enforces `concurrency` across all domains.
- The two compose: a run is bounded both overall and per-domain.

## Timeouts and retries

- Every network operation is wrapped in a timeout; a timeout is a recorded
  non-verdict, never a hang and never a false negative.
- SMTP 4xx/transient responses may be retried up to `smtp_retries` after a short
  backoff, then left indeterminate.

## Clock

- Time (for TTLs, backoff, rate limiting) comes from an injected clock, so tests
  are deterministic and fast without real sleeping.

## Provider interface

- `Provider` is a protocol with one job: given a `(name, domain)` or a domain,
  return known `(name, email)` samples it is aware of. It returns nothing by
  default and is never required.
- Providers are tried in chain order; the first with samples wins; the finder
  uses them for pattern detection.
- v1 ships the protocol and an empty chain. No provider implementation is
  included, and the core performs no request to any third party or any website.
- This is the seam through which an operator plugs in their own compliant data
  source later, keeping all data sourcing outside the library.

## Guarantees

- Nothing here reaches the network except DNS and SMTP to the domains the caller
  named. No telemetry. No bundled contact data. No implicit third-party calls.
