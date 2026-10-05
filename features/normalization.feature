Feature: Canonical form
  Reduce an address to the mailbox it really targets, using provider rules, so
  duplicates collapse. Never used for sending, only for comparison.

  Scenario Outline: Gmail ignores dots and subaddressing
    When I canonicalize "<input>"
    Then the canonical form is "<canonical>"

    Examples:
      | input                     | canonical          |
      | j.a.ne@gmail.com          | jane@gmail.com     |
      | jane+news@gmail.com       | jane@gmail.com     |
      | j.a.ne+news@gmail.com     | jane@gmail.com     |
      | jane@googlemail.com       | jane@gmail.com     |

  Scenario: An unknown provider's local part is left untouched
    When I canonicalize "j.a.ne@acme.com"
    Then the canonical form is "j.a.ne@acme.com"

  Scenario: The domain is lowercased for the canonical form
    When I canonicalize "Jane@ACME.com"
    Then the canonical form is "Jane@acme.com"

  Scenario: Two Gmail spellings of one mailbox compare equal
    When I canonicalize "j.a.ne+x@gmail.com"
    And I canonicalize "jane@gmail.com"
    Then both canonical forms are equal
