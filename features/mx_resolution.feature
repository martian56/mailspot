Feature: MX resolution
  Work out whether a domain can take mail, and where. No route means invalid;
  a DNS timeout doesn't.

  Scenario: A domain with MX records resolves to its mail hosts in preference order
    Given the domain "acme.com" has MX hosts:
      | preference | host                 |
      | 20         | alt.mail.acme.com    |
      | 10         | mail.acme.com        |
    When I verify "jane@acme.com"
    Then the MX check finds a mail route
    And the first mail host is "mail.acme.com"

  Scenario: A domain with no MX falls back to its address record
    Given the domain "small.com" has no MX records
    And the domain "small.com" has an A record
    When I verify "jane@small.com"
    Then the MX check finds a mail route
    And the mail route is recorded as an implicit A-record fallback

  Scenario: A domain with no mail route at all is invalid
    Given the domain "nomail.com" has no MX records
    And the domain "nomail.com" has no A record
    When I verify "jane@nomail.com"
    Then the status is "invalid"
    And the reason mentions no mail route

  Scenario: A non-existent domain is invalid
    Given the domain "nope.example" does not exist
    When I verify "jane@nope.example"
    Then the status is "invalid"

  Scenario: A transient DNS failure is not a verdict
    Given DNS for "acme.com" times out
    When I verify "jane@acme.com"
    Then the status is not "invalid"
    And the MX check is recorded as a transient failure

  Scenario: Google Workspace is fingerprinted from its MX hosts
    Given the domain "acme.com" has MX hosts:
      | preference | host                      |
      | 1          | aspmx.l.google.com        |
    When I verify "jane@acme.com"
    Then the detected mail provider is "google_workspace"

  Scenario: MX is resolved once for many addresses at the same domain
    Given the domain "acme.com" has MX hosts:
      | preference | host          |
      | 10         | mail.acme.com |
    When I verify these addresses:
      | jane@acme.com |
      | john@acme.com |
      | mary@acme.com |
    Then the domain "acme.com" is resolved for MX exactly once
