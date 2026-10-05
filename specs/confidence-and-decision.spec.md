# Confidence & Decision

How the raw check outputs become a `status`, a `confidence` score, and a
recommended `decision`. This is the only place that combines evidence into a
verdict, and it lives in orchestration, above the checks.

## Inputs

The outputs of every check that ran: syntax, MX, catch-all, SMTP, and the three
classification flags, plus whether each one ran at all.

## Status

The honest classification of the evidence:

- **invalid**: any hard disqualifier: bad syntax, `NXDOMAIN`, no mail route, or
  a 5xx SMTP rejection on a non-catch-all domain.
- **valid**: a 2xx SMTP acceptance on a domain proven *not* catch-all, with no
  disqualifier.
- **risky**: plausible but unproven: catch-all domain, or a role address, or an
  SMTP success on a domain whose catch-all status is unknown, or a disposable
  domain that is otherwise deliverable.
- **unknown**: syntax and MX are fine, but the decisive checks could not run
  (SMTP skipped/blocked and catch-all untested). Not enough to call either way.

Precedence is top-down: a hard disqualifier makes it `invalid` regardless of
anything else; otherwise the strongest available positive or risk signal wins.

## Confidence (0-100)

An additive model over the evidence, not a black box. Roughly:

- Syntax valid is the floor for any non-zero score.
- MX present adds meaningfully; a proven mail route is real evidence.
- A trustworthy SMTP acceptance (non-catch-all) is the largest single addition.
- A hard SMTP rejection drives confidence toward zero (high confidence that it
  is *bad*, reported as low usability).
- Missing evidence (SMTP skipped, catch-all untested) caps the score below the
  level a full, clean verification could reach. You cannot be highly confident
  on partial evidence.
- Risk flags (catch-all, role, disposable) apply defined reductions.

The exact weights are fixed in the implementation and covered by tests; the
contract here is the *ordering* and the *caps*: a clean non-catch-all acceptance
outscores an unknown, which outscores a catch-all, which outscores a hard
rejection; and no result built on a skipped SMTP check reaches the "confident
valid" band.

## Decision

The recommended action, derived from status and confidence:

| Decision | When |
|---|---|
| **send** | `valid`, high confidence, no blocking flag (not disposable, not role). |
| **verify_first** | `risky`, or valid-but-flagged (role), or confidence in the middle band: worth a lighter-weight confirmation before relying on it. |
| **skip** | `invalid`, or disposable, or confidence low enough that acting on it is not worthwhile. |
| **unknown** | `unknown` status: not enough evidence to recommend anything; the caller must decide or gather more. |

`decision` is a recommendation over the evidence, deliberately separate from
`status` so a caller can apply their own policy to the same facts.

## Reason

Every result carries one plain-language sentence naming the decisive factor:
"mailbox accepted on a non-catch-all domain", "domain is accept-all, cannot
confirm the specific mailbox", "no MX records for the domain", "SMTP blocked from
this host; result based on syntax and MX only". The reason always names what
actually drove the outcome, so a human can audit it.
