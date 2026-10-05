# SMTP Verification

Ask the mail server whether a specific mailbox exists, without sending anything.
It is the strongest single signal and also the least reliable, so when the answer
can be trusted matters as much as the probe itself.

## The probe

Open a connection to the domain's highest-preference mail host on port 25, speak
SMTP up to `RCPT TO`, and read the response code. No `DATA` is ever sent, so no
message is delivered.

1. Connect to the mail host (try hosts in MX preference order until one answers).
   The connection may go through a proxy (see `infrastructure.spec.md`).
2. `EHLO` with the configured sender hostname.
3. `MAIL FROM` with the configured sender address (the probe identity).
4. `RCPT TO` the address being checked.
5. Read the response, then `QUIT` cleanly.

Each step is recorded in a transcript (command plus response code) so a result
can be audited later.

## Provider-aware trust

Before trusting any answer, consult the provider strategy for the domain's
fingerprint (`provider-strategies.spec.md`). Providers fall into three cases:

- **Verifiable**: the server answers honestly. Trust a 2xx as deliverable and a
  5xx as not deliverable.
- **Known-unverifiable** (Gmail, Outlook/Office 365, Yahoo, AOL and the like):
  the server accepts almost every address and decides later, so a 2xx proves
  nothing. Do not probe for a verdict, and never report `valid` from SMTP here.
  The address comes back `risky`/`unknown` with a reason naming the provider.
- **Unknown provider**: probe and trust the answer, but let catch-all detection
  and scoring apply the usual caution.

This is the main defence against false positives, which are the worst outcome a
verifier can produce.

## Mapping responses

- **2xx** to `RCPT TO`: the server accepts the mailbox, deliverable (when the
  provider is verifiable and the domain is not catch-all).
- **5xx** (for example 550 "no such user"): hard rejection, not deliverable.
- **4xx** (greylisting, rate limiting, temporary): not a verdict. Retry up to the
  configured number of times with a short backoff. If it stays temporary, mark
  the address **deferred** so it can be re-checked later. Never treat a 4xx as
  invalid.
- Connection refused, reset, or timeout: no answer, recorded with the reason.

A deliverable result on a catch-all domain is not trusted. Catch-all is checked
first, and the real-mailbox probe is skipped on a catch-all domain.

## When SMTP is skipped

SMTP is best-effort and is skipped (with an explicit `skipped_reason`) when:

- the domain is catch-all (a per-mailbox answer would be meaningless),
- the provider is known-unverifiable (the answer would be worthless),
- SMTP is disabled in options,
- port 25 is not reachable and no proxy is configured.

A skip is never silent and never counted as success or failure. It lowers
confidence because evidence is missing, and the reason tells the caller the
headline rests on syntax, MX, and provider knowledge alone.

## Greylisting and the deferred outcome

A temporary refusal means "come back later," so the honest handling is to come
back later. Inline, mailspot retries a couple of times with short backoff. For
bulk, an address still temporary after the inline retries is returned as
`deferred`, and `recheck` re-runs only those addresses after a delay the caller
chooses (`bulk-processing.spec.md`). A deferred address is never invalid.

## The probe identity

The sender hostname and address used in `EHLO`/`MAIL FROM` are configurable and
default to a neutral, non-deceptive identity. They exist only to open the
conversation. The library never pretends to be a specific person and never sends
mail.

## Politeness and reputation

- One probe per address; the catch-all probe and the mailbox probe to the same
  host reuse the connection where the server permits.
- Per-domain rate limiting, with adaptive backoff when a host starts returning
  temporaries (`infrastructure.spec.md`), so hard probing does not get the
  egress address flagged.
- A proxy route, when configured, keeps probes off the host's own address and
  spreads them across egress addresses.
- Timeouts bound every stage of the conversation.

## Output

Populates `checks.smtp = { attempted, deliverable, code, reason, skipped_reason,
transcript }`.

- `attempted`: whether a probe was made.
- `deliverable`: `true` / `false` / `null` (null when no verdict).
- `code`: the SMTP response code, when one was received.
- `reason`: plain-language outcome.
- `skipped_reason`: populated only when `attempted` is false.
- `transcript`: the ordered command/response-code exchange, never any content.
