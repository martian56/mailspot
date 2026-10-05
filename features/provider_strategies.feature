Feature: Provider strategies
  Verification is branched on the mail provider. Providers that accept every
  probe never produce a confident "valid" from SMTP alone, which is how false
  positives are avoided.

  Scenario: A known-unverifiable provider is not probed for a verdict
    Given the domain "startup.com" is hosted on Google Workspace
    When I verify "jane@startup.com"
    Then the real-mailbox SMTP probe is skipped
    And the skip reason names the provider
    And the status is not "valid"

  Scenario: An address on consumer Gmail cannot be confirmed by SMTP
    When I verify "someone@gmail.com"
    Then the status is "risky"
    And the reason says the provider accepts every probe

  Scenario: A verifiable provider is trusted
    Given the domain "acme.com" is on a verifiable provider
    And "acme.com" is not a catch-all server
    And "jane@acme.com" is deliverable
    When I verify "jane@acme.com"
    Then the status is "valid"

  Scenario: An unknown provider is probed with normal caution
    Given the domain "acme.com" is on an unrecognized provider
    And "acme.com" is not a catch-all server
    And "jane@acme.com" is deliverable
    When I verify "jane@acme.com"
    Then the real-mailbox SMTP probe is attempted
    And the status is "valid"

  Scenario: A caller can override a provider strategy
    Given I mark "acme.com"'s provider as unverifiable via options
    When I verify "jane@acme.com"
    Then the real-mailbox SMTP probe is skipped
