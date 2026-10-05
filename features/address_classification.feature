Feature: Address classification
  mailspot flags addresses that change how a result should be read: disposable
  domains, role mailboxes, and free consumer providers. These are local checks
  with no network.

  Scenario: A disposable domain is flagged
    When I verify "jane@mailinator.com"
    Then the address is flagged as disposable

  Scenario: A role mailbox is flagged
    When I verify "support@acme.com"
    Then the address is flagged as a role address

  Scenario: A free-provider address is flagged
    When I verify "jane.doe@gmail.com"
    Then the address is flagged as free-provider

  Scenario: A normal business address carries no flags
    When I verify "jane.doe@acme.com"
    Then the address has no classification flags

  Scenario: A disposable address is not recommended even when deliverable
    Given the domain "mailinator.com" has a mail host that accepts every address checked as not catch-all
    And "jane@mailinator.com" is deliverable
    When I verify "jane@mailinator.com"
    Then the decision is "skip"

  Scenario: Classification lists can be extended by the caller
    Given "mycorp-temp.com" is added to the disposable list
    When I verify "jane@mycorp-temp.com"
    Then the address is flagged as disposable
