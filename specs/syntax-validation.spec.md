# Syntax Validation

The first check. Parse the address, normalize it, and decide whether it is
well-formed enough to be worth any network work. A hard syntax failure ends the
verification immediately.

## Behaviour

- Split the address into local part and domain on the last `@`.
- Reject an address with no `@`, an empty local part, an empty domain, or more
  than one unquoted `@`.
- Reject a domain with no dot, a leading/trailing dot, consecutive dots, or a
  label longer than 63 characters; reject a domain longer than 253 characters.
- Reject a local part longer than 64 characters.
- Reject characters not permitted in an unquoted local part. Quoted local parts
  (`"odd name"@x.com`) are accepted but flagged as unusual; they are legal but
  rare in business mail.
- Reject an address whose domain is an IP literal (`user@[192.168.0.1]`). Legal
  in the RFCs, out of scope here: these are not work addresses.

## Normalization

- Trim surrounding whitespace.
- Lowercase the domain (domains are case-insensitive).
- Leave the local part's case unchanged (the local part is technically
  case-sensitive), but record a lowercased form for comparison.
- Strip a single surrounding pair of angle brackets (`<jane@acme.com>`).

## Internationalization

- Accept internationalized domains (IDN) by converting the domain to its ASCII
  (punycode) form for later DNS work, while keeping the original for display.
- Accept UTF-8 local parts; do not attempt to transform them.

## Output

Populates `checks.syntax = { valid, normalized, reason }`.

- `valid`: boolean.
- `normalized`: the cleaned address used by every later step.
- `reason`: on failure, the specific rule that was broken, in plain language.

When `valid` is false, the overall result is `status=invalid`, `decision=skip`,
`confidence=0`, and no network check runs.

## Non-goals

- This check does not decide whether the mailbox exists or the domain accepts
  mail. It only decides whether the string is a plausible address. "Looks fine"
  is the most it can say.
