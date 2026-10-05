# Typo Suggestion

Catch a likely misspelling and suggest the intended address. This is most useful
at signup time, before an address is ever verified, to stop a bad one from being
entered at all. Offline, cheap, no network.

## Behaviour

- Split the address and look at the domain.
- Compare the domain against a list of common real domains and against the known
  free-provider list, using Damerau-Levenshtein distance (so a transposition like
  `gmial` to `gmail` counts as one edit).
- If a candidate is within a small distance (1, or 2 for longer domains) and the
  input domain is not already a known-good one, suggest the corrected address
  with the original local part.
- Also catch common wrong endings: `gmail.con`, `gmail.co`, `gmail.comm`,
  `gmail.cmo`, by checking the TLD against common ones the same way.
- Return nothing when the domain is already a known-good domain or nothing is
  close enough. No suggestion is the common case and is not an error.

## Scope and caution

- Suggestion is advisory. It never changes the address being verified; it only
  offers a correction for a human or a form to act on.
- It only suggests toward well-known domains. It will not invent a correction for
  a company domain it has never heard of, because the risk of a wrong suggestion
  there outweighs the benefit.
- It is a separate, synchronous function (`suggest(email) -> str | None`) and is
  also attached to a `VerificationResult` as `suggestion` when one applies.

## Data

`data/common_domains.txt` is the match list: the big free providers plus common
business and regional mail domains. It is plain, sorted, one per line, and
updatable, like the other lists.

## Non-goals

- Not a validator and not a deliverability check. A suggestion says "you may have
  meant this," nothing more.
