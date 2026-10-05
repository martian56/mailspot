Feature: Typo suggestion
  Catch a likely misspelled domain and suggest the intended address. Offline, no
  network, advisory only.

  Scenario Outline: Common domain typos are corrected
    When I ask for a suggestion for "<input>"
    Then the suggestion is "<corrected>"

    Examples:
      | input              | corrected          |
      | jane@gmial.com     | jane@gmail.com     |
      | jane@gmai.com      | jane@gmail.com     |
      | jane@gmail.con     | jane@gmail.com     |
      | jane@hotmial.com   | jane@hotmail.com   |
      | jane@outlok.com    | jane@outlook.com   |

  Scenario: A correct address gets no suggestion
    When I ask for a suggestion for "jane@gmail.com"
    Then there is no suggestion

  Scenario: An unknown company domain gets no suggestion
    When I ask for a suggestion for "jane@acme-industrial.com"
    Then there is no suggestion

  Scenario: A suggestion is attached to a verification result
    When I verify "jane@gmial.com"
    Then the result suggests "jane@gmail.com"
