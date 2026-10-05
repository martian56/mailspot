Feature: Syntax validation
  Parse and normalize the address first. Bad syntax ends it before any network.

  Scenario: A clean address passes and is normalized
    When I verify "Jane.Doe@Acme.COM"
    Then the syntax check passes
    And the normalized address is "Jane.Doe@acme.com"

  Scenario: An address without an at-sign is invalid
    When I verify "jane.doe.acme.com"
    Then the status is "invalid"
    And no network check is attempted
    And the reason mentions the missing "@"

  Scenario: An address with an empty local part is invalid
    When I verify "@acme.com"
    Then the status is "invalid"
    And no network check is attempted

  Scenario: A domain without a dot is invalid
    When I verify "jane@localhost"
    Then the status is "invalid"
    And no network check is attempted

  Scenario Outline: Malformed domains are rejected
    When I verify "<address>"
    Then the status is "invalid"
    And no network check is attempted

    Examples:
      | address             |
      | jane@acme..com      |
      | jane@.acme.com      |
      | jane@acme.com.      |

  Scenario: Surrounding angle brackets and whitespace are stripped
    When I verify "  <jane@acme.com>  "
    Then the syntax check passes
    And the normalized address is "jane@acme.com"

  Scenario: An internationalized domain is accepted and converted for DNS
    When I verify "jane@münchen.de"
    Then the syntax check passes
    And the domain used for DNS is "xn--mnchen-3ya.de"
