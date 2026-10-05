# Command-Line Interface

A thin front end over the public API. The CLI holds no verification logic of its
own; it parses arguments, calls the library, and formats output. Built with
`typer`.

## Commands

### `mailspot verify`
Verify one address.

```
mailspot verify jane.doe@acme.com
mailspot verify jane.doe@acme.com --json
mailspot verify jane.doe@acme.com --no-smtp
```

- Default output: a compact human-readable line: the address, the decision, the
  confidence, and the one-sentence reason.
- `--json`: the full `VerificationResult` as JSON.
- Flags mirror `Options`: `--no-smtp`, `--no-catch-all`, `--timeout`,
  `--concurrency`, `--rate`, `--probe-identity`.

### `mailspot find`
Find the likely address for a person.

```
mailspot find --name "Jane Doe" --domain acme.com
mailspot find --name "Jane Doe" --domain acme.com --json
mailspot find --name "Jane Doe" --domain acme.com --sample "John Roe=john.roe@acme.com"
```

- Default output: the best candidate with its confidence and the detected method,
  then the other candidates tried.
- `--sample` (repeatable): supply a known `(name, email)` pair for pattern
  detection.
- `--json`: the full `FinderResult`.

### `mailspot bulk`
Bulk verify or find from a CSV.

```
mailspot bulk verify contacts.csv --column email --out results.csv
mailspot bulk find people.csv --name-column name --domain-column domain --out results.csv
```

- Reads the named column(s), passes through the other columns, writes results as
  CSV (column order per `bulk-processing.spec.md`).
- Shows progress on stderr; the CSV goes to `--out` or stdout.
- Respects the same `Options` flags.

## Output conventions

- Human output goes to stdout; progress and diagnostics go to stderr, so piping
  the data output stays clean.
- `--json` emits valid JSON and nothing else on stdout.
- `--quiet` suppresses progress; `--verbose` adds per-check detail.

## Exit codes

- `0`: ran successfully (whatever the verification verdict). Verifying an
  address that turns out invalid is a successful run.
- `1`: usage error (bad arguments, unreadable file, bad options).
- `2`: the run could not complete (for example, no network at all).

The verdict about an address is data on stdout, not an exit code. The exit code
reports whether the *tool* worked, not whether the *mailbox* exists.

## Help

Every command and flag has a one-line help string. `mailspot --help` and
`mailspot <command> --help` are complete enough to use the tool without the docs.
