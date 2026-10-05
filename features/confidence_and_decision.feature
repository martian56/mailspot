Feature: Confidence and decision
  mailspot turns the evidence into a status, a 0-100 confidence score, and a
  recommended action. The score reflects how much is actually known, and missing
  evidence caps it.

  Scenario: A clean acceptance on a proven non-catch-all domain is a confident send
    Given "jane@acme.com" is deliverable on a non-catch-all domain
    When I verify "jane@acme.com"
    Then the status is "valid"
    And the decision is "send"
    And the confidence is at least 90

  Scenario: A hard rejection is a confident skip
    Given "ghost@acme.com" is hard-rejected on a non-catch-all domain
    When I verify "ghost@acme.com"
    Then the status is "invalid"
    And the decision is "skip"

  Scenario: A catch-all domain is risky and worth verifying first
    Given "jane@acme.com" is on a catch-all domain
    When I verify "jane@acme.com"
    Then the status is "risky"
    And the decision is "verify_first"

  Scenario: A blocked SMTP probe yields an honest unknown, not a guess
    Given the domain "acme.com" has a mail route
    And SMTP cannot be used from this host
    When I verify "jane@acme.com"
    Then the status is "unknown"
    And the confidence is below the confident-valid band
    And the reason says the result rests on syntax and MX only

  Scenario: A valid role address is suggested for confirmation, not blind sending
    Given "support@acme.com" is deliverable on a non-catch-all domain
    When I verify "support@acme.com"
    Then the status is "valid"
    And the decision is "verify_first"

  Scenario: Confidence ordering holds across outcomes
    Given a clean acceptance, an unknown, a catch-all, and a hard rejection
    Then the clean acceptance scores higher than the unknown
    And the unknown scores higher than the catch-all
    And the catch-all scores higher than the hard rejection
