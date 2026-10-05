Feature: Catch-all detection
  Check whether the domain accepts every address before trusting an SMTP hit.
  On an accept-all domain a success means nothing, so don't pretend otherwise.

  Background:
    Given the domain "acme.com" has a mail host "mail.acme.com"

  Scenario: A server that rejects a random address is not catch-all
    Given "mail.acme.com" rejects unknown addresses with code 550
    And "mail.acme.com" accepts "jane@acme.com"
    When I verify "jane@acme.com"
    Then the domain is found not to be catch-all
    And the SMTP check reports deliverable
    And the status is "valid"

  Scenario: A server that accepts a random address is catch-all
    Given "mail.acme.com" accepts every address
    When I verify "jane@acme.com"
    Then the domain is found to be catch-all
    And the real-mailbox SMTP probe is skipped
    And the status is "risky"
    And the reason mentions the domain is accept-all

  Scenario: The catch-all verdict is cached per domain
    Given "mail.acme.com" accepts every address
    When I verify these addresses:
      | jane@acme.com |
      | john@acme.com |
    Then the domain "acme.com" is catch-all tested exactly once

  Scenario: An indeterminate catch-all probe does not grant full confidence
    Given the catch-all probe to "mail.acme.com" times out
    And "mail.acme.com" accepts "jane@acme.com"
    When I verify "jane@acme.com"
    Then the catch-all status is recorded as unknown
    And the status is not "valid"
