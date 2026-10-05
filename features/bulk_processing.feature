Feature: Bulk processing
  mailspot verifies and finds in volume, preserving input order, collapsing
  duplicates, resolving each domain once, and never letting one bad row abort the
  batch.

  Scenario: Results come back aligned to input order
    Given a mail host that answers for "acme.com" and "globex.com"
    When I verify these addresses in order:
      | mary@globex.com |
      | jane@acme.com   |
      | john@acme.com   |
    Then the results are returned in the same order as the input

  Scenario: Duplicate addresses are verified once and shared
    Given a mail host that answers for "acme.com"
    When I verify these addresses:
      | jane@acme.com |
      | jane@acme.com |
    Then "jane@acme.com" is verified exactly once
    And both inputs receive a result

  Scenario: Each domain is resolved once across the batch
    Given a mail host that answers for "acme.com"
    When I verify these addresses:
      | jane@acme.com |
      | john@acme.com |
      | mary@acme.com |
    Then the domain "acme.com" is resolved for MX exactly once
    And the domain "acme.com" is catch-all tested exactly once

  Scenario: One failing row does not abort the batch
    Given a mail host that answers for "acme.com"
    And DNS for "broken.com" times out
    When I verify these addresses:
      | jane@acme.com   |
      | ghost@broken.com |
      | john@acme.com    |
    Then every input receives a result
    And the result for "ghost@broken.com" records a transient failure
    And the results for the "acme.com" addresses are unaffected

  Scenario: A whole batch streams results as they complete
    Given a mail host that answers for "acme.com"
    When I stream-verify 3 addresses at "acme.com"
    Then each result is yielded as it completes
    And each yielded result carries its input index

  Scenario: Recheck re-runs only the deferred rows
    Given a mail host that answers for "acme.com"
    And "greylist.com" defers every probe on the first attempt
    When I verify these addresses:
      | jane@acme.com      |
      | john@greylist.com  |
    And "greylist.com" accepts on a later attempt
    And I recheck the results
    Then only "john@greylist.com" is re-verified
    And "jane@acme.com" is passed through unchanged
