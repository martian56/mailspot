# Provider Strategies

Different mail providers answer SMTP probes differently, and treating them all
the same is why cheap verifiers are inaccurate. A provider strategy is a small
record, looked up from the domain's MX fingerprint, that tells the rest of the
pipeline how far to trust what the server says.

## Where a strategy comes from

MX resolution fingerprints the provider (`mx-resolution.spec.md`). The fingerprint
maps to a strategy from `data/providers.yaml`. An unrecognized provider gets the
default strategy. A caller can override or add strategies through
`provider_overrides` in `Options`.

## What a strategy says

- `name`: the provider, for example `google_workspace`, `microsoft365`, `yahoo`.
- `verifiable`: whether a `RCPT TO` answer from this provider can be trusted. For
  the big consumer and hosted providers that accept everything and decide after
  the body arrives, this is false.
- `catch_all_prone`: whether this provider commonly behaves as accept-all, so
  catch-all detection should be weighted accordingly.
- `notes`: a short reason, surfaced in the result so a human understands why the
  address could not be confirmed.

## How the pipeline uses it

- **SMTP**: if `verifiable` is false, the real-mailbox probe is skipped, because
  the answer would be meaningless. The reason records the provider.
- **Scoring**: a strategy with `verifiable` false caps confidence below the
  confident-valid band, so such an address never comes back `valid` on SMTP
  evidence alone. It lands `risky` or `unknown`.
- **Catch-all**: `catch_all_prone` informs how an indeterminate catch-all probe
  is treated.

## The data

`data/providers.yaml` holds the fingerprint patterns (MX host patterns) and the
strategy for each known provider. It is data, not code: adding a provider is a
data change, not a logic change. The known-unverifiable set includes at least
Google (Workspace and consumer Gmail), Microsoft (Office 365 and consumer
Outlook/Hotmail), Yahoo, and AOL, since these are the providers that have closed
the probe oracle.

## Non-goals

- The strategy holds no verification logic and makes no network calls. It is a
  lookup table that the checks and scoring read.
- It does not try to guess behaviour for an unknown provider beyond the safe
  default (probe, but let catch-all and scoring apply normal caution).
