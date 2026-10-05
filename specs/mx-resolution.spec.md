# MX Resolution

Find out whether a domain can receive mail at all, and which server handles it.
No MX means no delivery, which is a strong, cheap signal of an invalid address.

## Behaviour

- Resolve the domain's MX records via DNS.
- Order the hosts by MX preference (lowest number first); that order is the
  order later SMTP work tries them in.
- If there are no MX records, fall back to the domain's A/AAAA record, because
  the RFCs allow a domain with an address record but no MX to receive mail at
  that host. Record that this was an implicit fallback, not a real MX.
- If there is neither MX nor A/AAAA, the domain cannot receive mail.

## Provider fingerprinting

From the MX hostnames, identify the mail provider where it is unambiguous:
Google Workspace (`*.google.com`, `aspmx*`), Microsoft 365
(`*.outlook.com`, `*.protection.outlook.com`), and a small set of other common
ones. The provider name is advisory: it helps callers understand why SMTP may
behave a certain way (for example, Google greylisting probes). Unknown providers
are reported as `null`, not guessed.

## Caching

MX results are cached per domain for a configurable TTL (default 1 hour). A bulk
run over many addresses at the same domain resolves MX once.

## Failure handling

- A DNS timeout or servfail is not a verdict. It is recorded as a failed lookup
  with a reason, and MX is treated as unknown rather than absent. The score
  reflects missing evidence; the address is not called invalid on a transient
  DNS error.
- `NXDOMAIN` (the domain does not exist) *is* a verdict: no such domain means an
  invalid address.

## Output

Populates `checks.mx = { found, hosts, provider }`.

- `found`: true if MX or an A/AAAA fallback exists.
- `hosts`: the ordered list of mail hosts.
- `provider`: the fingerprinted provider name, or `null`.

When the domain resolves but has no mail route (and it was not a transient
error), the overall result is `status=invalid`, `decision=skip`.
