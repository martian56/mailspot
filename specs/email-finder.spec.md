# Email Finder

Given a person's name and a company domain, work out their most likely work
email and verify it. Two routes: infer the company's pattern from known
examples, or fall back to the common patterns. Every candidate is verified, and
the result is ranked.

## Inputs

- `name`: a person's name. Accept "Jane Doe", "Jane", "Doe, Jane", and names
  with middle names or hyphens; parse into first / middle / last as best as the
  input allows.
- `domain`: the company domain. A free-provider domain is rejected for finding,
  because a personal mailbox has no company pattern to infer.
- `samples` (optional): known `(name, email)` pairs at this domain, supplied by
  the caller or by a provider (see the provider interface). These drive pattern
  detection.

## Name parsing

- Normalize to ASCII for the local part (transliterate accents: `José` → `jose`),
  while keeping the original for display.
- Derive the parts used by patterns: `first`, `last`, `first_initial`,
  `last_initial`, and `middle`/`middle_initial` when present.
- Lowercase everything used in a local part.

## Pattern detection (preferred route)

When samples are available:

- For each sample, find which known pattern(s) produce its local part from its
  name.
- If the samples agree on one pattern, that is the detected pattern; apply it to
  the target name to produce the primary candidate.
- If samples disagree or are too few to be sure, record no confident detection
  and fall through to permutation, but rank any pattern that matched a sample
  above the rest.

## Permutation (fallback route)

With no usable samples, generate candidates from the common pattern catalogue,
ordered by real-world prevalence. The catalogue includes at least:

```
{first}.{last}      jane.doe@       (most common)
{first}{last}       janedoe@
{first_initial}{last}   jdoe@
{first}             jane@
{first}_{last}      jane_doe@
{first}-{last}      jane-doe@
{last}{first_initial}   doej@
{last}.{first}      doe.jane@
{first_initial}.{last}  j.doe@
{last}              doe@
```

The catalogue is data and extendable; the ordering encodes prevalence so the
first verified acceptance is usually the right answer.

## Verification and ranking

- Resolve MX and catch-all for the domain once, then verify candidates against
  that shared domain state.
- On a **non-catch-all** domain, probe candidates in prevalence order and stop at
  the first deliverable one. That is the `best` candidate, at high confidence.
- On a **catch-all** domain, SMTP cannot distinguish candidates. Return the
  most prevalent (or pattern-detected) candidate as `best` at `risky` /
  `verify_first`, and say clearly that the domain is accept-all so the address is
  a best guess, not a confirmation.
- Every generated candidate appears in `candidates` with its own
  `VerificationResult`, so the caller sees what was tried and why one won.

## Output

A `FinderResult`: `name`, `domain`, `best`, `candidates`, `detected_pattern`,
`method` (`pattern_detected` | `permutation`). `best` is `null` when no candidate
is credible (for example, a non-catch-all domain rejected every pattern).

## Non-goals

- The finder does not scrape or query the web to *discover* samples. Samples
  arrive from the caller or a provider the operator supplied. The core library
  only generates, verifies, and ranks.
