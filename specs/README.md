# Specs

What each part of mailspot is supposed to do. `overview.md` has the shared
vocabulary and the result model; `architecture.md` has the module layout and the
decisions made for scale. The rest is one file per capability, and each one has a
matching `.feature` with the concrete examples.

- `overview.md`: what it does, what it doesn't, the result types
- `architecture.md`: modules, data flow, async, caching, the provider seam
- `syntax-validation.spec.md` → `syntax_validation.feature`
- `mx-resolution.spec.md` → `mx_resolution.feature`
- `smtp-verification.spec.md` → `smtp_verification.feature`
- `catch-all-detection.spec.md` → `catch_all_detection.feature`
- `address-classification.spec.md` → `address_classification.feature`
- `confidence-and-decision.spec.md` → `confidence_and_decision.feature`
- `email-finder.spec.md` → `email_finder.feature`
- `bulk-processing.spec.md` → `bulk_processing.feature`
- `cli.spec.md` → `cli.feature`
- `infrastructure.spec.md`: options, cache, rate limiting, providers (unit-tested)
