# Normalization and Canonical Form

Two different ideas that are easy to confuse, so they are kept separate.

- **Normalized**: the cleaned version of exactly what the user typed, used by
  every check. Trim whitespace, strip angle brackets, lowercase the domain, keep
  the local part as given. Defined in `syntax-validation.spec.md`.
- **Canonical**: the mailbox the address really targets, after applying the
  provider's own rules. Used for deduplication and "same person" detection, never
  for sending. Defined here.

## Why canonical form matters

Some providers treat several written addresses as one mailbox. For a product
cleaning a list, `j.a.ne+news@gmail.com` and `jane@gmail.com` are the same person
and should collapse to one. Getting this right removes duplicates that a naive
comparison keeps.

## Rules

- **Gmail / Google Workspace**: dots in the local part are ignored, and anything
  from a `+` onward is a subaddress. `j.a.ne+news@gmail.com` canonicalizes to
  `jane@gmail.com`. `googlemail.com` folds to `gmail.com`.
- **Subaddressing generally**: many providers support `+` subaddressing (the tag
  after `+` routes to the base mailbox). Where a provider is known to, strip the
  `+tag`. Where it is unknown, leave the local part alone, because guessing could
  merge two real mailboxes.
- **Domain**: lowercased, IDN folded to its ASCII form, known aliases folded to
  their canonical domain.
- Everything else is left untouched. The rule is conservative: only fold what a
  provider is known to treat as equivalent.

## Output

- A synchronous `canonical(email) -> str`.
- The `canonical` field on `VerificationResult`.

When no provider-specific rule applies, the canonical form is just the normalized
address with a lowercased domain, so the field is always present and never guesses.

## Non-goals

- Canonical form is never used as the address to probe or to hand back for
  sending. The caller's original address is what gets verified; canonical is only
  for comparison and dedup.
