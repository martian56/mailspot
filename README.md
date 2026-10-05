# mailspot

Find and verify work email addresses. No API keys needed.

Two things:

- **Verify** an address: is it well-formed, does the domain take mail, and does the mailbox look real?
- **Find** someone's address from their name and company domain.

You get back a confidence score and a suggested action (`send`, `verify_first`, `skip`, `unknown`) instead of a bare yes/no, because the honest answer is usually "probably."

```python
import mailspot

result = await mailspot.verify("jane.doe@acme.com")
print(result.decision, result.confidence)   # send 94

guess = await mailspot.find("Jane Doe", "acme.com")
print(guess.best.email)                      # jane.doe@acme.com
```

```
$ mailspot verify jane.doe@acme.com
jane.doe@acme.com  valid  send  94  the server accepted the mailbox on a domain that is not accept-all

$ mailspot find --name "Jane Doe" --domain acme.com
jane.doe@acme.com  94  via permutation

$ mailspot suggest jane@gmial.com
jane@gmail.com
```

Other commands: `mailspot canonical`, `mailspot bulk verify in.csv --column email --out out.csv`, and `mailspot bulk recheck out.csv`. Every command takes `--json`.

Most existing packages only verify a single address, run synchronously, and quietly lie about catch-all domains. mailspot finds and verifies, runs checks concurrently, is provider-aware (it won't report a confident "valid" from Gmail or Outlook, which accept every probe), and is honest when it can't be sure.

Not on PyPI yet.

## SMTP is best-effort

Port 25 is blocked on most clouds and a lot of ISPs, and Google/Microsoft greylist probes. When mailspot can't get a straight answer over SMTP it says so in the result and falls back to what it does know (syntax, MX, catch-all, pattern). It won't make up certainty it doesn't have.

## Using it responsibly

mailspot does DNS and SMTP lookups you ask for, against domains you pick. It ships no contact data and collects nothing on its own. If you process data about real people you have obligations under GDPR, CAN-SPAM and the like. That's on you, the operator. The defaults are polite (bounded concurrency, per-domain rate limiting, timeouts); leave them that way unless you have a reason not to.

## Releasing

Bump `version` in `pyproject.toml`, commit, then tag and push:

```
git tag v0.2.0
git push origin v0.2.0
```

The publish workflow builds and uploads to PyPI on any `v*` tag, and fails if the
tag does not match the version in `pyproject.toml`, so the two never drift apart.

## License

MIT.

