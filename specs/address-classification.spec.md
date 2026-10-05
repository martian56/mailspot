# Address Classification

Three cheap, local flags that change how a result should be read. No network;
all from static, updatable lists shipped with the library.

## Flags

### disposable
The domain is a known throwaway / temporary-mail service. A syntactically and
technically valid disposable address is still near-useless for business contact,
so this flag strongly lowers the recommended action even when SMTP succeeds.

### role
The local part is a shared, non-personal mailbox: `info`, `sales`, `support`,
`admin`, `contact`, `hello`, `billing`, and similar. Role addresses are often
valid and deliverable but are not a specific person; they are flagged so the
caller can treat them differently (many outreach contexts exclude them).

### free_provider
The domain is a consumer mailbox provider: `gmail.com`, `outlook.com`,
`yahoo.com`, and the rest. Not negative in itself, but relevant: a free-provider
address is not a work address, which matters for B2B use and for pattern logic
in the finder (a company pattern cannot be inferred from a free domain).

## Data

- `data/disposable.txt`, `data/free.txt`, `data/roles.txt`: plain, sorted,
  one-entry-per-line lists, embedded in the package.
- Lists are matched case-insensitively.
- Lists are data, not code, and are expected to be updated over time; the
  matching logic does not change when the lists do.
- An option allows a caller to extend or override each list without editing the
  package.

## Output

Populates `flags = { disposable, role, free_provider }`: three booleans.

Classification never, on its own, makes an address `invalid`. It informs
scoring and the recommended decision. A disposable address may be perfectly
deliverable; the flag tells the caller it is probably not worth sending to.
