# Bulk Processing

Verify or find in volume, efficiently and politely. This is where the
resolve-once-per-domain and grouping decisions from the architecture pay off.

## Behaviour

- `verify_many(emails)` verifies a collection of addresses concurrently and
  returns a result per input.
- Input order is preserved in the returned collection, regardless of the order
  in which checks complete.
- Duplicates in the input are collapsed to one unit of work and the shared
  result is returned for each occurrence.

## Efficiency

- Addresses are grouped by domain. MX and catch-all are resolved once per
  domain and reused across every address at that domain.
- Within a domain, SMTP probes reuse a connection where the server allows it.
- A global concurrency cap bounds how many addresses are in flight at once; a
  per-domain rate limit bounds how hard any single server is hit.

## Streaming

- A streaming entry point yields each result as it completes, so memory does not
  grow with input size and output is produced continuously on long runs.
- The collecting entry point (`verify_many`) is a convenience over the stream
  for callers who want the whole list.

## Partial failure

- One address failing to verify never aborts the batch. Its result carries the
  failure as a normal `unknown`/`invalid` outcome with a reason.
- A whole-domain failure (DNS down for that domain) fails only that domain's
  addresses, each with the reason, and the rest of the batch proceeds.

## CSV (used by the CLI)

- Read addresses from a CSV: either a single-column file, or a named column in a
  multi-column file, passing other columns through to the output unchanged.
- Write results as CSV with a stable, documented column order: the input
  columns, then `email, status, decision, confidence, reason`, and the key check
  outcomes.
- The finder has an equivalent bulk form over `(name, domain)` rows.

## Output

`verify_many` → a list of `VerificationResult`, aligned to input order. The
streaming form → an async iterator of the same, in completion order, each
tagged with its input index so a caller can re-order if needed.
