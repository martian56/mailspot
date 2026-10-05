# Catch-All Detection

A catch-all (accept-all) domain accepts mail for every address, whether or not
the mailbox exists. On such a domain an SMTP probe always succeeds and therefore
proves nothing. Detecting this is what separates an honest verifier from one
that reports false positives.

## Behaviour

- Before probing the real mailbox, probe a random local part that is
  overwhelmingly unlikely to exist: a long random token at the same domain.
- If the server accepts that random address (2xx to `RCPT TO`), the domain is
  catch-all.
- If the server rejects it (5xx), the domain is not catch-all, and a later
  success on the real address is meaningful.
- If the probe is indeterminate (4xx, timeout, refused), catch-all status is
  unknown; this is recorded and the real-mailbox result is treated with the
  caution of an untested domain.

## Consequence

- **Catch-all = true** → the real-mailbox SMTP probe is skipped (it would be
  meaningless). The address cannot be confirmed; its best honest status is
  `risky`.
- **Catch-all = false** → proceed to the real-mailbox probe normally.
- **Catch-all = unknown** → proceed, but scoring does not grant full confidence
  to an SMTP success, because the domain's behaviour is not established.

## Caching

The catch-all verdict is cached per domain for a configurable TTL, so a bulk run
tests each domain once rather than once per address.

## Output

Populates `checks.catch_all = { tested, is_catch_all }`.

- `tested`: whether a catch-all probe was made.
- `is_catch_all`: `true` / `false` / `null` (null when untested or indeterminate).

## Non-goals

- This check does not try to distinguish a true catch-all from a server that
  simply defers all rejections to a later stage; both present as accept-all at
  `RCPT TO`, and both make a per-mailbox success untrustworthy, which is the
  only thing that matters here.
