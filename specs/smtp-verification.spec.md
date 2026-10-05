# SMTP Verification

Ask the mail server whether a specific mailbox exists, without sending anything.
This is the strongest single signal available, and also the least reliable, so
the behaviour around *when it can be trusted* matters as much as the probe.

## The probe

Open a connection to the domain's highest-preference mail host on port 25,
speak SMTP up to `RCPT TO`, and read the server's response code. No `DATA` is
ever sent, so no message is delivered.

The conversation:

1. Connect to the mail host (try hosts in MX preference order until one answers).
2. `EHLO` with the configured sender hostname.
3. `MAIL FROM` with the configured sender address (the "probe identity").
4. `RCPT TO` the address being checked.
5. Read the response, then `QUIT` cleanly.

## Mapping responses

- **2xx** to `RCPT TO` → the server accepts the mailbox: deliverable.
- **5xx** (e.g. 550 "no such user") → hard rejection: not deliverable.
- **4xx** (greylisting, rate limiting, temporary) → no answer; not a verdict.
  Optionally retried once after a short delay, then left as indeterminate.
- Connection refused / reset / timeout → no answer; recorded with the reason.

A deliverable result from a catch-all domain is *not* trusted (see
`catch-all-detection.spec.md`); catch-all is checked first and SMTP on a
catch-all domain is skipped as pointless.

## When SMTP is skipped

SMTP is best-effort and is skipped (with an explicit `skipped_reason`) when:

- the domain is catch-all (a per-mailbox answer would be meaningless),
- SMTP is disabled in options,
- port 25 egress is unavailable from the host running the library,
- the provider is known to refuse probes in a way that makes the answer
  worthless.

A skip is never silent and never counted as either success or failure. It lowers
confidence because evidence is missing, and it is reported so the caller knows
the headline rests on syntax, MX, and pattern alone.

## The probe identity

The sender hostname and address used in `EHLO`/`MAIL FROM` are configurable and
default to a neutral, clearly non-deceptive identity. They are used only to open
the conversation; the library never pretends to be a specific person or sends
mail.

## Politeness

- One probe per address; the catch-all probe and the mailbox probe to the same
  host reuse the connection where the server permits.
- Per-domain rate limiting applies.
- Timeouts bound every stage of the conversation.

## Output

Populates `checks.smtp = { attempted, deliverable, code, reason, skipped_reason }`.

- `attempted`: whether a probe was made.
- `deliverable`: `true` / `false` / `null` (null when no verdict).
- `code`: the SMTP response code, when one was received.
- `reason`: plain-language outcome.
- `skipped_reason`: populated only when `attempted` is false.
