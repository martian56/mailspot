Feature: SMTP verification
  Ask the server if a mailbox exists with RCPT TO, without sending anything.
  Best-effort: when there's no clear answer, say so.

  Background:
    Given the domain "acme.com" has a mail host "mail.acme.com"
    And "mail.acme.com" is not a catch-all server

  Scenario: An accepted mailbox on a non-catch-all domain is deliverable
    Given "mail.acme.com" accepts "jane@acme.com"
    When I verify "jane@acme.com"
    Then the SMTP check reports deliverable
    And no message is ever sent

  Scenario: A hard rejection means the mailbox does not exist
    Given "mail.acme.com" rejects "ghost@acme.com" with code 550
    When I verify "ghost@acme.com"
    Then the SMTP check reports not deliverable
    And the status is "invalid"

  Scenario: A greylisting response is retried then left indeterminate
    Given "mail.acme.com" replies to "jane@acme.com" with code 451
    When I verify "jane@acme.com"
    Then the SMTP probe is retried once
    And the SMTP check reports no verdict

  Scenario: SMTP is skipped when disabled, with a reason
    Given SMTP verification is disabled
    When I verify "jane@acme.com"
    Then the SMTP check is skipped
    And the skip reason mentions it was disabled

  Scenario: A connection timeout is a recorded non-verdict, not a rejection
    Given "mail.acme.com" does not answer on port 25
    When I verify "jane@acme.com"
    Then the SMTP check reports no verdict
    And the status is not "invalid"

  Scenario: The probe never sends message data
    Given "mail.acme.com" accepts "jane@acme.com"
    When I verify "jane@acme.com"
    Then the SMTP conversation stops after RCPT TO
    And the DATA command is never issued
