Feature: Command-line interface
  The CLI is a thin front end over the library: parse arguments, call the API,
  format output. The tool's exit code reports whether the run worked, not whether
  the mailbox exists.

  Scenario: Verify prints a human-readable line by default
    Given "jane@acme.com" is deliverable on a non-catch-all domain
    When I run "mailspot verify jane@acme.com"
    Then the output contains "jane@acme.com"
    And the output contains the decision "send"
    And the exit code is 0

  Scenario: The JSON flag emits the full result and nothing else on stdout
    Given "jane@acme.com" is deliverable on a non-catch-all domain
    When I run "mailspot verify jane@acme.com --json"
    Then stdout is valid JSON
    And the JSON has a "decision" field

  Scenario: Verifying an invalid address is still a successful run
    When I run "mailspot verify not-an-email"
    Then the output reports the address as invalid
    And the exit code is 0

  Scenario: Find prints the best candidate and the method
    Given "mail.acme.com" is not a catch-all server
    And "mail.acme.com" accepts only "jane.doe@acme.com"
    When I run "mailspot find --name 'Jane Doe' --domain acme.com"
    Then the output contains "jane.doe@acme.com"

  Scenario: Find accepts a sample for pattern detection
    Given "mail.acme.com" is not a catch-all server
    And "mail.acme.com" accepts "j.doe@acme.com"
    When I run "mailspot find --name 'Jane Doe' --domain acme.com --sample 'John Roe=j.roe@acme.com'"
    Then the output contains "j.doe@acme.com"

  Scenario: Bulk verify reads a column and writes a results CSV
    Given a CSV "contacts.csv" with an "email" column of 2 addresses
    And a mail host that answers for their domains
    When I run "mailspot bulk verify contacts.csv --column email --out results.csv"
    Then "results.csv" has a row per input
    And "results.csv" has the columns "email, status, decision, confidence, reason"

  Scenario: A usage error exits non-zero
    When I run "mailspot bulk verify missing-file.csv --column email"
    Then the exit code is 1
    And the error mentions the file could not be read

  Scenario: Progress goes to stderr so piped data stays clean
    Given "jane@acme.com" is deliverable on a non-catch-all domain
    When I run "mailspot verify jane@acme.com --json" and capture streams separately
    Then stdout contains only the JSON
    And any progress output is on stderr
